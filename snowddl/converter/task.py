from json import loads

from snowddl.blueprint import ObjectType
from snowddl.converter.abc_converter import ConvertResult
from snowddl.converter.abc_schema_object_converter import AbstractSchemaObjectConverter
from snowddl.converter._yaml import YamlLiteralStr
from snowddl.parser.task import task_json_schema


class TaskConverter(AbstractSchemaObjectConverter):
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
                "when": r["condition"],
                "body": r["definition"],
                "schedule": r["schedule"],
                "after": r["predecessors"],
                "warehouse": r["warehouse"],
                "allow_overlapping_execution": r["allow_overlapping_execution"],
                "error_integration": r["error_integration"],
                "config": r["config"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def dump_object(self, row):
        """
        The following parameters are currently not available for conversion due to lack of data
        in SHOW TASKS and DESC TASK commands output:
        - session_params
        - user_task_timeout_ms
        - suspend_task_after_num_failures
        - finalize
        """
        data = {
            "body": YamlLiteralStr(row["body"]),
            "schedule": row["schedule"],
            "after": self._get_after(row),
            "when": row["when"],
            "warehouse": row["warehouse"],
            "user_task_managed_initial_warehouse_size": self._get_user_task_managed_initial_warehouse_size(row),
            "allow_overlapping_execution": self._get_allow_overlapping_execution(row),
            "error_integration": self._get_error_integration(row),
            "config": row["config"],
            "comment": row["comment"],
        }

        object_path = (
            self.base_path / self._normalise_name_with_prefix(row["database"]) / self._normalise_name(row["schema"]) / "task"
        )

        if data:
            self._dump_file(object_path / f"{self._normalise_name(row['name'])}.yaml", data, task_json_schema)
            return ConvertResult.DUMP

        return ConvertResult.EMPTY

    def _get_user_task_managed_initial_warehouse_size(self, row):
        if row["warehouse"]:
            return None

        return "XSMALL"

    def _get_allow_overlapping_execution(self, row):
        if row["allow_overlapping_execution"] == "true":
            return True

        if row["allow_overlapping_execution"] == "false":
            return False

        return None

    def _get_error_integration(self, row):
        if row["error_integration"] == "null":
            return None

        return row["error_integration"]

    def _get_after(self, row):
        if "after" not in row:
            return None

        after = [self._normalise_name_with_prefix(n) for n in loads(row["after"])]

        if len(after) == 0:
            return None

        return after
