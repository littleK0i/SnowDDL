from snowddl.blueprint import DynamicTableBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class DynamicTableResolver(AbstractSchemaObjectResolver):
    # Dynamic tables are available for all accounts during preview, including STANDARD edition
    # skip_min_edition = Edition.ENTERPRISE
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.DYNAMIC_TABLE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW DYNAMIC TABLES IN SCHEMA {database:i}.{schema:i}",
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
                "owner": r["owner"],
                # Extract SQL query text only, skip the initial "CREATE DYNAMIC TABLE ..." part
                # Snowflake modifies original SQL text in this column, it cannot be compared directly
                "text": r["text"].partition("\nAS\n")[2],
                "target_lag": r["target_lag"],
                "refresh_mode": r["refresh_mode"],
                "warehouse": r["warehouse"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(DynamicTableBlueprint)

    def create_object(self, bp: DynamicTableBlueprint):
        query = self.engine.query_builder()
        query.append("CREATE OR REPLACE")

        if bp.is_transient:
            query.append("TRANSIENT")

        query.append(
            "DYNAMIC TABLE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        query.append(self._build_common_dynamic_table_sql(bp))

        self.engine.execute_safe_ddl(query)

        return ResolveResult.CREATE

    def compare_object(self, bp: DynamicTableBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if bp.text != row["text"]:
            query = self.engine.query_builder()
            query.append("CREATE OR REPLACE")

            if bp.is_transient:
                query.append("TRANSIENT")

            query.append(
                "DYNAMIC TABLE {full_name:i}",
                {
                    "full_name": bp.full_name,
                },
            )

            query.append(self._build_common_dynamic_table_sql(bp))
            self.engine.execute_unsafe_ddl(query)

            return ResolveResult.REPLACE

        if bp.target_lag != row["target_lag"]:
            self.engine.execute_safe_ddl(
                "ALTER DYNAMIC TABLE {full_name:i} SET TARGET_LAG = {target_lag}",
                {
                    "full_name": bp.full_name,
                    "target_lag": bp.target_lag,
                },
            )

            result = ResolveResult.ALTER

        if str(bp.warehouse) != row["warehouse"]:
            self.engine.execute_safe_ddl(
                "ALTER DYNAMIC TABLE {full_name:i} SET WAREHOUSE = {warehouse:i}",
                {
                    "full_name": bp.full_name,
                    "warehouse": bp.warehouse,
                },
            )

            result = ResolveResult.ALTER

        if bp.comment != row["comment"]:
            self.engine.execute_safe_ddl(
                "ALTER DYNAMIC TABLE {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
            )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP DYNAMIC TABLE {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_common_dynamic_table_sql(self, bp: DynamicTableBlueprint):
        query = self.engine.query_builder()

        if bp.columns:
            query.append_nl("(")

            for idx, c in enumerate(bp.columns):
                query.append_nl(
                    "    {comma:r}{col_name:i}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "col_name": c.name,
                    },
                )

                if c.comment:
                    query.append(
                        "COMMENT {col_comment}",
                        {
                            "col_comment": c.comment,
                        },
                    )

            query.append_nl(")")

        query.append_nl(
            "TARGET_LAG = {target_lag}",
            {
                "target_lag": bp.target_lag,
            },
        )

        query.append_nl(
            "WAREHOUSE = {warehouse:i}",
            {
                "warehouse": bp.warehouse,
            },
        )

        if bp.refresh_mode:
            query.append_nl(
                "REFRESH_MODE = {refresh_mode}",
                {
                    "refresh_mode": bp.refresh_mode,
                },
            )

        if bp.initialize:
            query.append_nl(
                "INITIALIZE = {initialize}",
                {
                    "initialize": bp.initialize,
                },
            )

        if bp.cluster_by:
            query.append_nl(
                "CLUSTER BY ({cluster_by:r})",
                {
                    "cluster_by": bp.cluster_by,
                },
            )

        if bp.retention_time is not None:
            query.append_nl(
                "DATA_RETENTION_TIME_IN_DAYS = {retention_time:d}",
                {
                    "retention_time": bp.retention_time,
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
        query.append_nl(bp.text)

        return query
