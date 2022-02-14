from itertools import islice
from re import compile

from snowddl.blueprint import TableBlueprint, TableColumn, DataType, BaseDataType
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType

cluster_by_syntax_re = compile(r'^(\w+)?\((.*)\)$')


class TableResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.TABLE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW TABLES IN SCHEMA {database:i}.{schema:i}", {
            "database": schema['database'],
            "schema": schema['schema'],
        })

        for r in cur:
            # Skip external tables
            if r['is_external'] == 'Y':
                continue

            full_name = f"{r['database_name']}.{r['schema_name']}.{r['name']}"
            existing_objects[full_name] = {
                "database": r['database_name'],
                "schema": r['schema_name'],
                "name": r['name'],
                "owner": r['owner'],
                "is_transient": r['kind'] == 'TRANSIENT',
                "cluster_by": r['cluster_by'] if r['cluster_by'] else None,
                "change_tracking": bool(r['change_tracking'] == 'ON'),
                "search_optimization": bool(r.get('search_optimization') == 'ON'),
                "comment": r['comment'] if r['comment'] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(TableBlueprint)

    def create_object(self, bp: TableBlueprint):
        query = self._build_create_table(bp)
        self.engine.execute_safe_ddl(query)

        if bp.search_optimization:
            self.engine.execute_safe_ddl("ALTER TABLE {full_name:i} ADD SEARCH OPTIMIZATION", {
                "full_name": bp.full_name,
            })

        return ResolveResult.CREATE

    def compare_object(self, bp: TableBlueprint, row: dict):
        alters = []
        is_replace_required = False

        bp_cols = {str(c.name): c for c in bp.columns}
        snow_cols = self._get_existing_columns(bp)

        remaining_col_names = list(snow_cols.keys())

        for col_name, snow_c in snow_cols.items():
            # Drop columns which do not exist in blueprint
            if col_name not in bp_cols:
                alters.append(self.engine.format("DROP COLUMN {col_name:i}", {
                    "col_name": col_name,
                }))

                remaining_col_names.remove(col_name)
                continue

            bp_c = bp_cols[col_name]

            # Set or drop NOT NULL constraint
            if snow_c.not_null and not bp_c.not_null:
                alters.append(self.engine.format("MODIFY COLUMN {col_name:i} DROP NOT NULL", {
                    "col_name": col_name,
                }))
            elif not snow_c.not_null and bp_c.not_null:
                alters.append(self.engine.format("MODIFY COLUMN {col_name:i} SET NOT NULL", {
                    "col_name": col_name,
                }))

            # Default
            if snow_c.default != bp_c.default:
                # DROP DEFAULT is supported
                if snow_c.default is not None and bp_c.default is None:
                    alters.append(self.engine.format("MODIFY COLUMN {col_name:i} DROP DEFAULT", {
                        "col_name": col_name,
                    }))

                # Switch to another sequence is supported
                elif isinstance(snow_c.default, str) and snow_c.default.upper().endswith('.NEXTVAL') \
                and isinstance(bp_c.default, str) and bp_c.default.upper().endswith('.NEXTVAL'):
                    alters.append(self.engine.format("MODIFY COLUMN {col_name:i} SET DEFAULT {default:r}", {
                        "col_name": col_name,
                        "default": bp_c.default,
                    }))

                # All other DEFAULT changes are not supported
                else:
                    is_replace_required = True

            # Comments
            if snow_c.comment != bp_c.comment:
                # UNSET COMMENT is currently not supported for columns, we can only set it to empty string
                alters.append(self.engine.format("MODIFY COLUMN {col_name:i} COMMENT {comment}", {
                    "col_name": col_name,
                    "comment": bp_c.comment if bp_c.comment else '',
                }))

            # If type matches exactly, skip all other checks
            if snow_c.type == bp_c.type:
                continue

            # Only a few optimized MODIFY COLUMN ... TYPE actions are supported
            # https://docs.snowflake.com/en/sql-reference/sql/alter-table-column.html
            if snow_c.type.base_type == bp_c.type.base_type:
                # Increase or decrease precision of NUMBER, but not scale
                if snow_c.type.base_type == BaseDataType.NUMBER \
                and snow_c.type.val1 != bp_c.type.val2 \
                and snow_c.type.val2 == bp_c.type.val2:
                    alters.append(self.engine.format("MODIFY COLUMN {col_name:i} TYPE {col_type:r}", {
                        "col_name": col_name,
                        "col_type": bp_c.type,
                    }))

                    continue

                if snow_c.type.base_type == BaseDataType.VARCHAR \
                and snow_c.type.val1 < bp_c.type.val1:
                    alters.append(self.engine.format("MODIFY COLUMN {col_name:i} TYPE {col_type:r}", {
                        "col_name": col_name,
                        "col_type": bp_c.type,
                    }))

                    continue

            # All other transformations require full table replace
            is_replace_required = True

        # Remaining column names exactly match initial part of blueprint column names
        if remaining_col_names == list(islice(bp_cols.keys(), 0, len(remaining_col_names))):
            # Get remaining part of blueprint columns
            for col_name, bp_c in islice(bp_cols.items(), len(remaining_col_names), None):
                query = self.engine.query_builder()
                query.append("ADD COLUMN {col_name:i} {col_type:r}", {
                    "col_name": col_name,
                    "col_type": bp_c.type,
                })

                if bp_c.default is not None:
                    query.append("DEFAULT {default}", {
                        "default": bp_c.default,
                    })

                if bp_c.not_null:
                    query.append("NOT NULL")

                if bp_c.comment:
                    query.append("COMMENT {comment}", {
                        "comment": bp_c.comment,
                    })

                alters.append(query)
        else:
            # Reordering of columns is not supported
            is_replace_required = True

        # Changing TRANSIENT tables to permanent and back are not supported
        if bp.is_transient != row['is_transient']:
            is_replace_required = True

        # Clustering key
        if not self._compare_cluster_by(bp, row):
            if bp.cluster_by:
                alters.append(self.engine.format("CLUSTER BY ({cluster_by:r})", {
                    "cluster_by": bp.cluster_by,
                }))
            else:
                alters.append(self.engine.format("DROP CLUSTERING KEY"))

        # Change tracking
        if bp.change_tracking != row['change_tracking']:
            alters.append(self.engine.format("SET CHANGE_TRACKING = {change_tracking:b}", {
                "change_tracking": bp.change_tracking,
            }))

        # Search optimization
        if bp.search_optimization and not row['search_optimization']:
            alters.append("ADD SEARCH OPTIMIZATION")
        elif not bp.search_optimization and row['search_optimization']:
            alters.append("DROP SEARCH OPTIMIZATION")

        # Comment
        if bp.comment != row['comment']:
            if bp.comment:
                alters.append(self.engine.format("SET COMMENT = {comment}", {
                    "comment": bp.comment,
                }))
            else:
                alters.append(self.engine.format("UNSET COMMENT"))

        if is_replace_required:
            self.engine.execute_unsafe_ddl(self._build_create_table(bp, snow_cols), condition=self.engine.settings.execute_replace_table)

            if bp.search_optimization:
                self.engine.execute_safe_ddl("ALTER TABLE {full_name:i} ADD SEARCH OPTIMIZATION", {
                    "full_name": bp.full_name,
                })

            return ResolveResult.REPLACE
        elif alters:
            for alter in alters:
                self.engine.execute_unsafe_ddl("ALTER TABLE {full_name:i} {alter:r}", {
                    "full_name": bp.full_name,
                    "alter": alter,
                })

            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl("DROP TABLE {database:i}.{schema:i}.{table_name:i}", {
            "database": row['database'],
            "schema": row['schema'],
            "table_name": row['name'],
        })

        return ResolveResult.DROP

    def _get_existing_columns(self, bp: TableBlueprint):
        existing_columns = {}

        cur = self.engine.execute_meta("DESC TABLE {full_name:i}", {
            "full_name": bp.full_name,
        })

        for r in cur:
            existing_columns[r['name']] = TableColumn(
                name=r['name'],
                type=DataType(r['type']),
                not_null=bool(r['null?'] == 'N'),
                default=r['default'] if r['default'] else None,
                comment=r['comment'] if r['comment'] else None,
            )

        return existing_columns

    def _build_create_table(self, bp: TableBlueprint, snow_cols=None):
        query = self.engine.query_builder()
        query.append("CREATE")

        if snow_cols:
            query.append("OR REPLACE")

        if bp.is_transient:
            query.append("TRANSIENT")

        query.append("TABLE {full_name:i}", {
            "full_name": bp.full_name,
        })

        query.append_nl("(")

        for idx, c in enumerate(bp.columns):
            query.append_nl("    {comma:r}{col_name:i} {col_type:r}", {
                "comma": "  " if idx == 0 else ", ",
                "col_name": c.name,
                "col_type": c.type,
            })

            if c.default is not None:
                query.append("DEFAULT {default:r}", {
                    "default": c.default,
                })

            if c.not_null:
                query.append("NOT NULL")

            if c.comment:
                query.append("COMMENT {comment}", {
                    "comment": c.comment,
                })

        query.append_nl(")")

        if bp.cluster_by:
            query.append_nl("CLUSTER BY ({cluster_by:r})", {
                "cluster_by": bp.cluster_by,
            })

        if bp.change_tracking:
            query.append_nl("CHANGE_TRACKING = TRUE")

        if bp.retention_time is not None:
            query.append_nl("DATA_RETENTION_TIME_IN_DAYS = {retention_time:d}", {
                "retention_time": bp.retention_time
            })

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        if snow_cols:
            query.append_nl("COPY GRANTS")
            query.append_nl("AS")
            query.append_nl("SELECT")

            for idx, c in enumerate(bp.columns):
                if str(c.name) in snow_cols:
                    query.append_nl("    {comma:r}{col_name:i}::{col_type:r} AS {col_name:i}", {
                        "comma": "  " if idx == 0 else ", ",
                        "col_name": c.name,
                        "col_type": c.type,
                    })
                else:
                    query.append_nl("    {comma:r}{col_val}::{col_type:r} AS {col_name:i}", {
                        "comma": "  " if idx == 0 else ", ",
                        "col_name": c.name,
                        "col_type": c.type,
                        "col_val": c.default,
                    })

            query.append_nl("FROM {full_name:i}", {
                "full_name": bp.full_name,
            })

        return query

    def _compare_cluster_by(self, bp: TableBlueprint, row: dict):
        bp_cluster_by = ', '.join(bp.cluster_by) if bp.cluster_by else None
        snow_cluster_by = cluster_by_syntax_re.sub(r'\2', row['cluster_by']) if row['cluster_by'] else None

        return bp_cluster_by == snow_cluster_by
