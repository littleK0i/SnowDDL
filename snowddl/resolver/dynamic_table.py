from json import loads as json_loads

from snowddl.blueprint import DynamicTableBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class DynamicTableResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    unit_to_seconds_multiplier = {
        "second": 1,
        "seconds": 1,
        "minute": 60,
        "minutes": 60,
        "hour": 3600,
        "hours": 3600,
        "day": 86400,
        "days": 86400,
    }

    def get_object_type(self) -> ObjectType:
        return ObjectType.DYNAMIC_TABLE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW AS RESOURCE DYNAMIC TABLES IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            r = json_loads(r["As Resource"])

            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "owner": r["owner"],
                "is_transient": r["kind"] == "TRANSIENT",
                "retention_time": r["data_retention_time_in_days"],
                "columns": r["columns"],
                "text": r["query"].rstrip(";"),
                "cluster_by": r["cluster_by"],
                "target_lag": r["target_lag"],
                "refresh_mode": r["refresh_mode"],
                "warehouse": r["warehouse"],
                "comment": r["comment"],
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
        replace_reasons = []

        if bp.columns and [str(c.name) for c in bp.columns] != [str(c["name"]) for c in row["columns"]]:
            replace_reasons.append("Column definition was changed")

        if bp.text != row["text"]:
            replace_reasons.append("SQL text was changed")

        if bp.is_transient is True and row["is_transient"] is False:
            replace_reasons.append("Dynamic table type was changed to TRANSIENT")
        elif bp.is_transient is False and row["is_transient"] is True:
            replace_reasons.append("Dynamic table type was changed to PERMANENT")

        if bp.refresh_mode and bp.refresh_mode != "AUTO" and bp.refresh_mode != row["refresh_mode"]:
            replace_reasons.append(f"Refresh mode was changed to {bp.refresh_mode}")

        if replace_reasons:
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
            self.engine.execute_unsafe_ddl("\n".join(f"-- {r}" for r in replace_reasons) + "\n" + str(query))

            return ResolveResult.REPLACE

        if not self._compare_target_lag(bp, row):
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

        if not self._compare_cluster_by(bp, row):
            if bp.cluster_by:
                self.engine.execute_unsafe_ddl(
                    "ALTER DYNAMIC TABLE {full_name:i} CLUSTER BY ({cluster_by:r})",
                    {
                        "full_name": bp.full_name,
                        "cluster_by": bp.cluster_by,
                    },
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER DYNAMIC TABLE {full_name:i} DROP CLUSTERING KEY",
                    {"full_name": bp.full_name},
                )

            result = ResolveResult.ALTER

        if bp.retention_time is not None and bp.retention_time != row["retention_time"]:
            self.engine.execute_unsafe_ddl(
                "ALTER DYNAMIC TABLE {full_name:i} SET DATA_RETENTION_TIME_IN_DAYS = {retention_time:d}",
                {
                    "full_name": bp.full_name,
                    "retention_time": bp.retention_time,
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

        for idx, c in enumerate(row["columns"]):
            bp_col_comment = bp.columns[idx].comment if bp.columns else None

            if bp_col_comment != c["comment"]:
                if bp_col_comment:
                    self.engine.execute_safe_ddl(
                        "ALTER DYNAMIC TABLE {full_name:i} MODIFY COLUMN {column_name:i} COMMENT {comment}",
                        {
                            "full_name": bp.full_name,
                            "column_name": c["name"],
                            "comment": bp_col_comment,
                        },
                    )
                else:
                    self.engine.execute_safe_ddl(
                        "ALTER DYNAMIC TABLE {full_name:i} MODIFY COLUMN {column_name:i} UNSET COMMENT",
                        {
                            "full_name": bp.full_name,
                            "column_name": c["name"],
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

    def _compare_cluster_by(self, bp: DynamicTableBlueprint, row: dict):
        bp_cluster_by = ", ".join(bp.cluster_by).upper() if bp.cluster_by else None
        snow_cluster_by = ", ".join(row["cluster_by"]).upper() if row["cluster_by"] else None

        return bp_cluster_by == snow_cluster_by

    def _compare_target_lag(self, bp: DynamicTableBlueprint, row: dict):
        if bp.target_lag == "DOWNSTREAM":
            return row["target_lag"]["type"] == "DOWNSTREAM"

        num, _, unit = bp.target_lag.partition(" ")

        num = int(num)
        unit = unit.lower()

        num_in_seconds = num * self.unit_to_seconds_multiplier[unit]

        if row["target_lag"]["type"] == "USER_DEFINED" and row["target_lag"]["seconds"] == num_in_seconds:
            return True

        return False
