from re import compile

from snowddl.blueprint import (
    Ident,
    DataType,
    HybridTableBlueprint,
    SchemaObjectIdent,
    TableColumn,
)
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType

collate_type_syntax_re = compile(r"^(.*) COLLATE \'(.*)\'$")


class HybridTableResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.HYBRID_TABLE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW HYBRID TABLES IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            full_name = f"{r['database_name']}.{r['schema_name']}.{r['name']}"
            existing_objects[full_name] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "owner": r["owner"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(HybridTableBlueprint)

    def create_object(self, bp: HybridTableBlueprint):
        common_query = self._build_common_hybrid_table(bp)
        create_query = self.engine.query_builder()

        create_query.append(
            "CREATE HYBRID TABLE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        create_query.append_nl(common_query)

        self.engine.execute_safe_ddl(create_query)
        self.engine.execute_safe_ddl(
            "COMMENT ON TABLE {full_name:i} IS {comment}",
            {
                "full_name": bp.full_name,
                "comment": common_query.add_short_hash(bp.comment),
            },
        )

        return ResolveResult.CREATE

    def compare_object(self, bp: HybridTableBlueprint, row: dict):
        common_query = self._build_common_hybrid_table(bp)

        if not common_query.compare_short_hash(row["comment"]):
            replace_query = self.engine.query_builder()

            replace_query.append(
                "CREATE OR REPLACE HYBRID TABLE {full_name:i}",
                {
                    "full_name": bp.full_name,
                },
            )

            replace_query.append_nl(common_query)
            replace_query.append_nl(self._build_replace_select_hybrid_table(bp, self._get_existing_columns(bp)))

            self.engine.execute_unsafe_ddl(replace_query, condition=self.engine.settings.execute_replace_table)

            self.engine.execute_unsafe_ddl(
                "COMMENT ON TABLE {full_name:i} IS {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": common_query.add_short_hash(bp.comment),
                },
                condition=self.engine.settings.execute_replace_table,
            )

            return ResolveResult.REPLACE

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP TABLE {database:i}.{schema:i}.{table_name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "table_name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_common_hybrid_table(self, bp: HybridTableBlueprint):
        query = self.engine.query_builder()
        query.append("(")

        for idx, c in enumerate(bp.columns):
            query.append_nl(
                "    {comma:r}{col_name:i} {col_type:r}",
                {
                    "comma": "  " if idx == 0 else ", ",
                    "col_name": c.name,
                    "col_type": c.type,
                },
            )

            if c.collate:
                query.append(
                    "COLLATE {collate}",
                    {
                        "collate": c.collate,
                    },
                )

            if c.default is not None:
                query.append(
                    "DEFAULT {default:r}",
                    {
                        "default": self._normalize_bp_default(c.default),
                    },
                )

            if c.not_null:
                query.append("NOT NULL")

            if c.expression:
                query.append(
                    "AS ({expression:r})",
                    {
                        "expression": c.expression,
                    },
                )

            if c.comment:
                query.append(
                    "COMMENT {comment}",
                    {
                        "comment": c.comment,
                    },
                )

        # Primary key
        query.append_nl(
            "    , PRIMARY KEY ({columns:i}) COMMENT {comment}",
            {
                "columns": bp.primary_key,
                "comment": self.get_object_type().name,
            },
        )

        # Unique keys
        if bp.unique_keys:
            for unique_key in bp.unique_keys:
                query.append_nl(
                    "    , UNIQUE ({columns:i}) COMMENT {comment}",
                    {
                        "columns": unique_key,
                        "comment": self.get_object_type().name,
                    },
                )

        # Foreign keys
        if bp.foreign_keys:
            for foreign_key in bp.foreign_keys:
                query.append_nl(
                    "    , FOREIGN KEY ({columns:i}) REFERENCES {ref_table_name:i} ({ref_columns:i}) COMMENT {comment}",
                    {
                        "columns": foreign_key.columns,
                        "ref_table_name": foreign_key.ref_table_name,
                        "ref_columns": foreign_key.ref_columns,
                        "comment": self.get_object_type().name,
                    },
                )

        if bp.indexes:
            for idx in bp.indexes:
                index_name = "__".join(str(part) for part in ["INDEX"] + idx.columns)

                # Snowflake bug: Index name must be used without quotes, otherwise it is actually stored with quotes
                query.append_nl(
                    "    , INDEX {index_name:r} ({columns:i})",
                    {
                        "index_name": index_name,
                        "columns": idx.columns,
                    },
                )

                if idx.include:
                    query.append(
                        "INCLUDE ({include:i})",
                        {
                            "include": idx.include,
                        },
                    )

        query.append_nl(")")

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        return query

    def _build_replace_select_hybrid_table(self, bp: HybridTableBlueprint, snow_cols: dict):
        query = self.engine.query_builder()

        query.append("AS")
        query.append_nl("SELECT")

        for idx, c in enumerate(bp.columns):
            col_name = str(c.name)

            if col_name in snow_cols:
                # Column already exist

                if c.type == snow_cols[col_name].type:
                    # Column has the same type
                    query.append_nl(
                        "    {comma:r}{col_name:i} AS {col_name:i}",
                        {
                            "comma": "  " if idx == 0 else ", ",
                            "col_name": c.name,
                        },
                    )
                else:
                    # Column has a different type, add type cast
                    query.append_nl(
                        "    {comma:r}{col_name:i}::{col_type:r} AS {col_name:i}",
                        {
                            "comma": "  " if idx == 0 else ", ",
                            "col_name": c.name,
                            "col_type": c.type,
                        },
                    )
            else:
                # Column does not exist, use default value with type cast
                query.append_nl(
                    "    {comma:r}{col_val}::{col_type:r} AS {col_name:i}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "col_name": c.name,
                        "col_type": c.type,
                        "col_val": c.default,
                    },
                )

        query.append_nl(
            "FROM {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        return query

    def _get_existing_columns(self, bp: HybridTableBlueprint):
        existing_columns = {}

        cur = self.engine.execute_meta(
            "DESC TABLE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        for r in cur:
            m = collate_type_syntax_re.match(r["type"])

            if m:
                dtype = m.group(1)
                collate = m.group(2)
            else:
                dtype = r["type"]
                collate = None

            existing_columns[r["name"]] = TableColumn(
                name=Ident(r["name"]),
                type=DataType(dtype),
                not_null=bool(r["null?"] == "N"),
                default=r["default"] if r["default"] else None,
                expression=r["expression"] if r["expression"] else None,
                collate=collate,
                comment=r["comment"] if r["comment"] else None,
            )

        return existing_columns

    def _normalize_bp_default(self, bp_default):
        if isinstance(bp_default, SchemaObjectIdent):
            # This cannot be formatted properly with double-quotes ("), Snowflake strips it from DEFAULT value returned by DESC TABLE
            return f"{bp_default}.NEXTVAL"

        return bp_default
