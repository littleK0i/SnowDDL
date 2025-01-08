from snowddl.blueprint import StreamBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class StreamResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.STREAM

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW STREAMS IN SCHEMA {database:i}.{schema:i}",
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
                "object_type": r["source_type"],
                "object_name": r["table_name"],
                "type": r["type"],
                "stale": r["stale"] == "true",
                "mode": r["mode"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(StreamBlueprint)

    def create_object(self, bp: StreamBlueprint):
        query = self._build_create_stream_sql(bp)
        self.engine.execute_safe_ddl(query)

        return ResolveResult.CREATE

    def compare_object(self, bp: StreamBlueprint, row: dict):
        replace_reasons = []

        if row["stale"]:
            replace_reasons.append(f"Stream is marked as stale")

        if bp.object_type.singular_for_ref != row["object_type"].upper().replace(" ", "_"):
            replace_reasons.append(f"Source object type [{str(bp.object_type.name)}] in config does not match source type [{row['object_type']}] in Snowflake")

        if bp.object_name != row["object_name"]:
            replace_reasons.append(f"Source object name [{bp.object_name}] in config does not match source name [{row['object_name']}] in Snowflake")

        if bp.append_only != ("APPEND_ONLY" in row["mode"]):
            replace_reasons.append(f"APPEND_ONLY={str(bp.append_only)} in config does not match mode [{row['mode']}] in Snowflake")

        if bp.insert_only != ("INSERT_ONLY" in row["mode"]):
            replace_reasons.append(f"INSERT_ONLY={str(bp.insert_only)} in config does not match mode [{row['mode']}] in Snowflake")

        if replace_reasons:
            query = self._build_create_stream_sql(bp, True)
            query_with_comment = "\n".join(f"-- {r}" for r in replace_reasons) + "\n" + str(query)

            self.engine.execute_unsafe_ddl(query_with_comment)
            return ResolveResult.REPLACE

        if bp.comment != row["comment"]:
            self.engine.execute_safe_ddl(
                "ALTER STREAM {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
            )

            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP STREAM {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_create_stream_sql(self, bp: StreamBlueprint, is_replace=False):
        query = self.engine.query_builder()
        query.append("CREATE")

        if is_replace:
            query.append("OR REPLACE")

        query.append(
            "STREAM {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        # TODO: uncomment when COPY GRANTS is supported for streams
        # https://docs.snowflake.com/en/sql-reference/sql/create-stream.html
        # query.append_nl("COPY GRANTS")

        query.append_nl(
            "ON {object_type:r} {object_name:i}",
            {
                "object_type": bp.object_type.singular,
                "object_name": bp.object_name,
            },
        )

        if bp.append_only:
            query.append_nl("APPEND_ONLY = TRUE")

        if bp.insert_only:
            query.append_nl("INSERT_ONLY = TRUE")

        if bp.show_initial_rows:
            query.append_nl("SHOW_INITIAL_ROWS = TRUE")

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        return query
