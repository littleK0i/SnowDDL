from snowddl.blueprint import TaskBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class TaskResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.TASK

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW TASKS IN SCHEMA {database:i}.{schema:i}",
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
                "predecessors": r["predecessors"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(TaskBlueprint)

    def create_object(self, bp: TaskBlueprint):
        query = self._build_create_task(bp)

        self.engine.execute_safe_ddl(query)

        self.engine.execute_safe_ddl(
            "COMMENT ON TASK {full_name:i} IS {comment}",
            {
                "full_name": bp.full_name,
                "comment": query.add_short_hash(bp.comment),
            },
        )

        return ResolveResult.CREATE

    def compare_object(self, bp: TaskBlueprint, row: dict):
        query = self._build_create_task(bp)

        if not query.compare_short_hash(row["comment"]):
            self.engine.execute_safe_ddl(query)

            self.engine.execute_safe_ddl(
                "COMMENT ON TASK {full_name:i} IS {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": query.add_short_hash(bp.comment),
                },
            )

            return ResolveResult.REPLACE

        # Set predecessor again if it was dropped
        if bp.after and not row["predecessors"]:
            self.engine.execute_safe_ddl(
                "ALTER TASK {full_name:i} ADD AFTER {after:i}",
                {
                    "full_name": bp.full_name,
                    "after": bp.after,
                },
            )

            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl(
            "DROP TASK {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_create_task(self, bp: TaskBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE OR REPLACE TASK {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        if bp.warehouse:
            query.append_nl(
                "WAREHOUSE = {warehouse:i}",
                {
                    "warehouse": bp.warehouse,
                },
            )

        if bp.user_task_managed_initial_warehouse_size:
            query.append_nl(
                "USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = {size:r}",
                {
                    "size": bp.user_task_managed_initial_warehouse_size,
                },
            )

        if bp.schedule:
            query.append_nl(
                "SCHEDULE = {schedule}",
                {
                    "schedule": bp.schedule,
                },
            )

        if bp.scheduling_mode:
            query.append_nl(
                "SCHEDULING_MODE = {scheduling_mode}",
                {
                    "scheduling_mode": bp.scheduling_mode,
                },
            )

        if bp.config:
            query.append_nl(
                "CONFIG = {config}",
                {
                    "config": bp.config,
                },
            )

        if bp.allow_overlapping_execution:
            query.append_nl(
                "ALLOW_OVERLAPPING_EXECUTION = {allow_overlapping_execution:b}",
                {
                    "allow_overlapping_execution": bp.allow_overlapping_execution,
                },
            )

        if bp.user_task_timeout_ms:
            query.append_nl(
                "USER_TASK_TIMEOUT_MS = {timeout:d}",
                {
                    "timeout": bp.user_task_timeout_ms,
                },
            )

        if bp.suspend_task_after_num_failures:
            query.append_nl(
                "SUSPEND_TASK_AFTER_NUM_FAILURES = {suspend_task_after_num_failures:d}",
                {
                    "suspend_task_after_num_failures": bp.suspend_task_after_num_failures,
                },
            )

        if bp.error_integration:
            query.append_nl(
                "ERROR_INTEGRATION = {error_integration:i}",
                {
                    "error_integration": bp.error_integration,
                },
            )

        if bp.success_integration:
            query.append_nl(
                "SUCCESS_INTEGRATION = {success_integration:i}",
                {
                    "success_integration": bp.success_integration,
                },
            )

        if bp.log_level:
            query.append_nl(
                "LOG_LEVEL = {log_level}",
                {
                    "log_level": bp.log_level,
                },
            )

        if bp.task_auto_retry_attempts:
            query.append_nl(
                "TASK_AUTO_RETRY_ATTEMPTS = {task_auto_retry_attempts:d}",
                {
                    "task_auto_retry_attempts": bp.task_auto_retry_attempts,
                },
            )

        if bp.user_task_minimum_trigger_interval_in_seconds:
            query.append_nl(
                "USER_TASK_MINIMUM_TRIGGER_INTERVAL_IN_SECONDS = {user_task_minimum_trigger_interval_in_seconds:d}",
                {
                    "user_task_minimum_trigger_interval_in_seconds": bp.user_task_minimum_trigger_interval_in_seconds,
                },
            )

        if bp.target_completion_interval:
            query.append_nl(
                "TARGET_COMPLETION_INTERVAL = {target_completion_interval}",
                {
                    "target_completion_interval": bp.target_completion_interval,
                },
            )

        if bp.serverless_task_min_statement_size:
            query.append_nl(
                "SERVERLESS_TASK_MIN_STATEMENT_SIZE = {serverless_task_min_statement_size}",
                {
                    "serverless_task_min_statement_size": bp.serverless_task_min_statement_size,
                },
            )

        if bp.serverless_task_max_statement_size:
            query.append_nl(
                "SERVERLESS_TASK_MAX_STATEMENT_SIZE = {serverless_task_max_statement_size}",
                {
                    "serverless_task_max_statement_size": bp.serverless_task_max_statement_size,
                },
            )

        if bp.session_params:
            for param_name, param_value in bp.session_params.items():
                query.append_nl(
                    "{param_name:r} = {param_value:dp}",
                    {
                        "param_name": param_name,
                        "param_value": param_value,
                    },
                )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        if bp.after:
            query.append_nl("AFTER {after:i}", {"after": bp.after})

        if bp.finalize:
            query.append_nl("FINALIZE = {finalize:i}", {"finalize": bp.finalize})

        if bp.when:
            query.append_nl("WHEN {when:r}", {"when": bp.when})

        # Not supported by Snowflake, but documented
        # query.append_nl("COPY GRANTS")

        query.append_nl("AS")
        query.append_nl(bp.body)

        return query
