from re import compile, DOTALL

from snowddl.blueprint import ObjectType
from snowddl.converter.abc_converter import ConvertResult
from snowddl.converter.abc_schema_object_converter import AbstractSchemaObjectConverter
from snowddl.converter._yaml import YamlLiteralStr
from snowddl.parser.task import task_json_schema
import json


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
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def dump_object(self, row):
        data = {
            "body": YamlLiteralStr(row["body"]),
            "schedule": row["schedule"] if "schedule" in row else None,
            "after": self._get_after(row),
            "when": row["when"] if "when" in row else None,
            "warehouse": row["warehouse"] if "warehouse" in row else None,
            "user_task_managed_initial_warehouse_size": "XSMALL" if "warehouse" is None else None,
            "allow_overlapping_execution": self._get_allow_overlapping_execution(row),
            "comment": row["comment"] if "comment" in row else None,
        }

        object_path = (
            self.base_path / self._normalise_name_with_prefix(row["database"]) / self._normalise_name(row["schema"]) / "task"
        )
        object_path.mkdir(mode=0o755, parents=True, exist_ok=True)

        if data:
            self._dump_file(object_path / f"{self._normalise_name(row['name'])}.yaml", data, task_json_schema)
            return ConvertResult.DUMP

        return ConvertResult.EMPTY

    def _get_allow_overlapping_execution(self, row):
        if "allow_overlapping_execution" not in row or row["allow_overlapping_execution"] == "null":
            return None
        else: 
            return (row["allow_overlapping_execution"] == "true");

    def _get_after(self, row):
        if "after" not in row:
            return None
        after = [self._normalise_name_with_prefix(n) for n in json.loads(row["after"])]
        if len(after) == 0:
            return None
        return after

    