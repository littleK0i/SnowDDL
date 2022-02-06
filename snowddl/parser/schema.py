from snowddl.blueprint import SchemaBlueprint, Ident, IdentWithPrefix, ComplexIdentWithPrefix
from snowddl.parser.abc_parser import AbstractParser
from snowddl.parser.database import database_json_schema


schema_json_schema = {
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


class SchemaParser(AbstractParser):
    def load_blueprints(self):
        for database_path in self.base_path.iterdir():
            if not database_path.is_dir():
                continue

            database_params = self.parse_single_file(database_path / 'params.yaml', database_json_schema)

            for schema_path in database_path.iterdir():
                if not schema_path.is_dir():
                    continue

                schema_params = self.parse_single_file(schema_path / 'params.yaml', schema_json_schema)

                combined_params = {
                    "is_transient": database_params.get('is_transient', False) or schema_params.get('is_transient', False),
                    "retention_time": schema_params.get("retention_time"),
                }

                bp = SchemaBlueprint(
                    full_name=ComplexIdentWithPrefix(self.env_prefix, database_path.name, schema_path.name),
                    database=IdentWithPrefix(self.env_prefix, database_path.name),
                    schema=Ident(schema_path.name),
                    is_transient=combined_params.get('is_transient', False),
                    retention_time=combined_params.get('retention_time', None),
                    is_sandbox=schema_params.get('is_sandbox', False),
                    comment=schema_params.get('comment', None),
                )

                self.config.add_blueprint(bp)
