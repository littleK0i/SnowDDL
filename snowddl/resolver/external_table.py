from snowddl.blueprint import ExternalTableBlueprint, ExternalTableColumn, DataType, BaseDataType
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType
from snowddl.resolver._utils import coalesce


class ExternalTableResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.EXTERNAL_TABLE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW EXTERNAL TABLES IN SCHEMA {database:i}.{schema:i}", {
            "database": schema['database'],
            "schema": schema['schema'],
        })

        for r in cur:
            full_name = f"{r['database_name']}.{r['schema_name']}.{r['name']}"
            existing_objects[full_name] = {
                "database": r['database_name'],
                "schema": r['schema_name'],
                "name": r['name'],
                "owner": r['owner'],
                "invalid": r['invalid'],
                "invalid_reason": r['invalid_reason'],
                "stage": r['stage'],
                "location": r['location'],
                "file_format_name": r['file_format_name'],
                "file_format_type": r['file_format_type'],
                "notification_channel": r['notification_channel'],
                "comment": r['comment'] if r['comment'] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(ExternalTableBlueprint)

    def create_object(self, bp: ExternalTableBlueprint):
        query = self._build_create_external_table(bp)

        self.engine.execute_safe_ddl(query)

        self.engine.execute_safe_ddl("COMMENT ON TABLE {full_name:i} IS {comment}", {
            "full_name": bp.full_name,
            "comment": query.add_short_hash(bp.comment),
        })

        return ResolveResult.CREATE

    def compare_object(self, bp: ExternalTableBlueprint, row: dict):
        query = self._build_create_external_table(bp)

        if not query.compare_short_hash(row['comment']):
            self.engine.execute_safe_ddl(query)

            self.engine.execute_safe_ddl("COMMENT ON TABLE {full_name:i} IS {comment}", {
                "full_name": bp.full_name,
                "comment": query.add_short_hash(bp.comment),
            })

            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl("DROP EXTERNAL TABLE {database:i}.{schema:i}.{table_name:i}", {
            "database": row['database'],
            "schema": row['schema'],
            "table_name": row['name'],
        })

        return ResolveResult.DROP

    def _build_create_external_table(self, bp: ExternalTableBlueprint):
        query = self.engine.query_builder()

        query.append("CREATE OR REPLACE EXTERNAL TABLE {full_name:i}", {
            "full_name": bp.full_name,
        })

        if bp.columns:
            query.append_nl("(")

            for idx, c in enumerate(bp.columns):
                query.append_nl("    {comma:r}{col_name:i} {col_type:r} AS ({col_expr:r})", {
                    "comma": "  " if idx == 0 else ", ",
                    "col_name": c.name,
                    "col_type": c.type,
                    "col_expr": c.expr,
                })

                if c.not_null:
                    query.append("NOT NULL")

                if c.comment:
                    query.append("COMMENT {comment}", {
                        "comment": c.comment,
                    })

            query.append_nl(")")

        if bp.partition_by:
            query.append_nl("PARTITION BY ({partition_by:i})", {
                "partition_by": bp.partition_by,
            })

        query.append_nl("LOCATION = @{stage_name:i}{path:r}", {
            "stage_name": bp.location_stage,
            "path": coalesce(bp.location_path, ''),
        })

        if bp.location_pattern:
            query.append_nl("PATTERN = {pattern}", {
                "pattern": bp.location_pattern,
            })

        query.append_nl("FILE_FORMAT = (FORMAT_NAME = {file_format:i})", {
            "file_format": bp.file_format,
        })

        if bp.refresh_on_create is not None:
            query.append_nl("REFRESH_ON_CREATE = {refresh_on_create:b}", {
                "refresh_on_create": bp.refresh_on_create,
            })

        if bp.auto_refresh is not None:
            query.append_nl("AUTO_REFRESH = {auto_refresh:b}", {
                "auto_refresh": bp.auto_refresh,
            })

        if bp.aws_sns_topic:
            query.append_nl("AWS_SNS_TOPIC = {aws_sns_topic}", {
                "aws_sns_topic": bp.aws_sns_topic,
            })

        if bp.integration:
            query.append_nl("INTEGRATION = {integration:i}", {
                "integration": bp.integration,
            })

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        query.append_nl("COPY GRANTS")

        return query
