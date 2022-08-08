from snowddl.blueprint import TaskBlueprint, AccountObjectIdent, SchemaObjectIdent, build_schema_object_ident
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


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
        "when": {
            "type": "string"
        },
        "warehouse": {
            "type": "string"
        },
        "user_task_managed_initial_warehouse_size": {
            "type": "string"
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
        "comment": {
            "type": "string"
        }
    },
    "additionalProperties": False
}


class TaskParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("task", task_json_schema, self.process_task)

    def process_task(self, f: ParsedFile):
        if f.params.get('after'):
            tasks_after = [build_schema_object_ident(self.env_prefix, t, f.database, f.schema) for t in f.params.get('after')]
        else:
            tasks_after = None

        bp = TaskBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            body=f.params['body'],
            schedule=f.params.get('schedule'),
            after=tasks_after,
            depends_on=tasks_after if tasks_after else [],
            when=f.params.get('when'),
            warehouse=AccountObjectIdent(self.env_prefix, f.params['warehouse']) if f.params.get('warehouse') else None,
            user_task_managed_initial_warehouse_size=f.params.get('user_task_managed_initial_warehouse_size'),
            allow_overlapping_execution=f.params.get('allow_overlapping_execution'),
            session_params=self.normalise_params_dict(f.params.get('session_params')),
            user_task_timeout_ms=f.params.get('user_task_timeout_ms'),
            comment=f.params.get('comment'),
        )

        self.config.add_blueprint(bp)
