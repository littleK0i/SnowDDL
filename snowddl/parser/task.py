from snowddl.blueprint import Ident, TaskBlueprint, AccountObjectIdent, SchemaObjectIdent, build_schema_object_ident
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
task_json_schema = {
    "type": "object",
    "properties": {
        "body": {
            "type": "string"
        },
        "schedule": {
            "type": "string"
        },
        "after": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "finalize": {
            "type": "string",
        },
        "when": {
            "type": "string"
        },
        "warehouse": {
            "type": "string"
        },
        "user_task_managed_initial_warehouse_size": {
            "type": "string"
        },
        "config": {
            "type": "string",
        },
        "allow_overlapping_execution": {
            "type": "boolean"
        },
        "session_params": {
            "type": "object",
            "additionalProperties": {
                "type": ["boolean", "number", "string"]
            }
        },
        "user_task_timeout_ms": {
            "type": "integer"
        },
        "suspend_task_after_num_failures": {
            "type": "integer"
        },
        "error_integration": {
            "type": "string"
        },
        "task_auto_retry_attempts": {
            "type": "integer"
        },
        "user_task_minimum_trigger_interval_in_seconds": {
            "type": "integer"
        },
        "comment": {
            "type": "string"
        }
    },
    "additionalProperties": False
}
# fmt: on


class TaskParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("task", task_json_schema, self.process_task)

    def process_task(self, f: ParsedFile):
        after = None
        finalize = None
        depends_on = set()

        if f.params.get("after"):
            after = [build_schema_object_ident(self.env_prefix, t, f.database, f.schema) for t in f.params.get("after")]
            depends_on.update(after)

        if f.params.get("finalize"):
            finalize = build_schema_object_ident(self.env_prefix, f.params.get("finalize"), f.database, f.schema)
            depends_on.add(finalize)

        bp = TaskBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            body=f.params["body"],
            schedule=f.params.get("schedule"),
            after=after,
            finalize=finalize,
            depends_on=depends_on,
            when=f.params.get("when"),
            warehouse=AccountObjectIdent(self.env_prefix, f.params["warehouse"]) if f.params.get("warehouse") else None,
            user_task_managed_initial_warehouse_size=f.params.get("user_task_managed_initial_warehouse_size"),
            config=f.params.get("config"),
            allow_overlapping_execution=f.params.get("allow_overlapping_execution"),
            session_params=self.normalise_params_dict(f.params.get("session_params")),
            user_task_timeout_ms=f.params.get("user_task_timeout_ms"),
            suspend_task_after_num_failures=f.params.get("suspend_task_after_num_failures"),
            error_integration=Ident(f.params.get("error_integration")) if f.params.get("error_integration") else None,
            task_auto_retry_attempts=f.params.get("task_auto_retry_attempts"),
            user_task_minimum_trigger_interval_in_seconds=f.params.get("user_task_minimum_trigger_interval_in_seconds"),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
