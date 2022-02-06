from snowddl.blueprint import TaskBlueprint, Ident, IdentWithPrefix, ComplexIdentWithPrefix
from snowddl.parser.abc_parser import AbstractParser


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
            "type": "string"
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
        for f in self.parse_schema_object_files("task", task_json_schema):
            if f.params.get('after'):
                task_after_ident = self.config.build_complex_ident(f.params['after'], f.database, f.schema)
            else:
                task_after_ident = None

            bp = TaskBlueprint(
                full_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, f.name),
                database=IdentWithPrefix(self.env_prefix, f.database),
                schema=Ident(f.schema),
                name=Ident(f.name),
                body=f.params['body'],
                schedule=f.params.get('schedule'),
                after=task_after_ident,
                depends_on=[task_after_ident] if task_after_ident else [],
                when=f.params.get('when'),
                warehouse=IdentWithPrefix(self.env_prefix, f.params['warehouse']) if f.params.get('warehouse') else None,
                user_task_managed_initial_warehouse_size=f.params.get('user_task_managed_initial_warehouse_size'),
                allow_overlapping_execution=f.params.get('allow_overlapping_execution'),
                session_params=self.normalise_params_dict(f.params.get('session_params')),
                user_task_timeout_ms=f.params.get('user_task_timeout_ms'),
                comment=f.params.get('comment'),
            )

            self.config.add_blueprint(bp)
