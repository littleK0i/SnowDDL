from snowddl.blueprint import DatabaseBlueprint, DatabaseIdent
from snowddl.parser.abc_parser import AbstractParser


database_json_schema = {
    "type": "object",
    "properties": {
        "is_transient": {
            "type": "boolean"
        },
        "retention_time": {
            "type": "integer"
        },
        "is_sandbox": {
            "type": "boolean"
        },
        "comment": {
            "type": "string"
        }
    },
    "additionalProperties": False
}


class DatabaseParser(AbstractParser):
    def load_blueprints(self):
        for database_path in self.base_path.iterdir():
            if not database_path.is_dir():
                continue

            params = self.parse_single_file(database_path / 'params.yaml', database_json_schema)

            bp = DatabaseBlueprint(
                full_name=DatabaseIdent(self.env_prefix, database_path.name),
                is_transient=params.get('is_transient', False),
                retention_time=params.get('retention_time', None),
                is_sandbox=params.get('is_sandbox', False),
                comment=params.get('comment', None),
            )

            self.config.add_blueprint(bp)
