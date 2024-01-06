from snowddl.blueprint import PipeBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType
from snowddl.resolver._utils import coalesce


class PipeResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.PIPE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW PIPES IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "definition": r["definition"],
                "integration": r["integration"],
                "pattern": r["pattern"],
                "comment": r["comment"],
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(PipeBlueprint)

    def create_object(self, bp: PipeBlueprint):
        common_query = self._build_common_pipe_sql(bp)
        create_query = self.engine.query_builder()

        create_query.append(
            "CREATE PIPE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        create_query.append(common_query)

        self.engine.execute_safe_ddl(create_query)

        self.engine.execute_safe_ddl(
            "COMMENT ON PIPE {full_name:i} IS {comment}",
            {
                "full_name": bp.full_name,
                "comment": common_query.add_short_hash(bp.comment),
            },
        )

        return ResolveResult.CREATE

    def compare_object(self, bp: PipeBlueprint, row: dict):
        common_query = self._build_common_pipe_sql(bp)

        if not common_query.compare_short_hash(row["comment"]):
            replace_query = self.engine.query_builder()

            replace_query.append(
                "CREATE OR REPLACE PIPE {full_name:i}",
                {
                    "full_name": bp.full_name,
                },
            )

            replace_query.append(common_query)

            self.engine.execute_unsafe_ddl(replace_query)

            self.engine.execute_unsafe_ddl(
                "COMMENT ON PIPE {full_name:i} IS {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": common_query.add_short_hash(bp.comment),
                },
            )

            return ResolveResult.REPLACE

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP PIPE {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_common_pipe_sql(self, bp: PipeBlueprint):
        query = self.engine.query_builder()

        query.append_nl(
            "AUTO_INGEST = {auto_ingest:b}",
            {
                "auto_ingest": bp.auto_ingest,
            },
        )

        if bp.aws_sns_topic:
            query.append_nl(
                "AWS_SNS_TOPIC = {aws_sns_topic}",
                {
                    "aws_sns_topic": bp.aws_sns_topic,
                },
            )

        if bp.integration:
            query.append_nl(
                "INTEGRATION = {integration:i}",
                {
                    "integration": bp.integration,
                },
            )

        if bp.error_integration:
            query.append_nl(
                "ERROR_INTEGRATION = {error_integration:i}",
                {
                    "error_integration": bp.error_integration,
                },
            )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        query.append_nl("AS")
        query.append_nl(self._build_copy_into(bp))

        return query

    def _build_copy_into(self, bp: PipeBlueprint):
        query = self.engine.query_builder()

        query.append(
            "COPY INTO {table_name:i}",
            {
                "table_name": bp.copy_table_name,
            },
        )

        if bp.copy_transform:
            query.append(" (")

            for idx, col_name in enumerate(bp.copy_transform):
                query.append_nl(
                    "    {comma:r}{col_name:i}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "col_name": col_name,
                    },
                )

            query.append_nl(") FROM (")
            query.append_nl("    SELECT")

            for idx, col_expr in enumerate(bp.copy_transform.values()):
                query.append_nl(
                    "        {comma:r}{col_expr:r}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "col_expr": col_expr,
                    },
                )

            query.append_nl(
                "    FROM @{stage_name:i}{path:r}",
                {
                    "stage_name": bp.copy_stage_name,
                    "path": coalesce(bp.copy_path, ""),
                },
            )

            query.append_nl(")")
        else:
            query.append_nl(
                "FROM @{stage_name:i}{path:r}",
                {
                    "stage_name": bp.copy_stage_name,
                    "path": coalesce(bp.copy_path, ""),
                },
            )

        if bp.copy_pattern:
            query.append_nl(
                "PATTERN = {pattern}",
                {
                    "pattern": bp.copy_pattern,
                },
            )

        if bp.copy_file_format:
            query.append_nl(
                "FILE_FORMAT = {file_format:i}",
                {
                    "file_format": bp.copy_file_format,
                },
            )

        if bp.copy_options:
            for k, v in bp.copy_options.items():
                query.append_nl(
                    "{option_name:r} = {option_value:dp}",
                    {
                        "option_name": k,
                        "option_value": v,
                    },
                )

        return query
