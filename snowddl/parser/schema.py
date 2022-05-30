from snowddl.blueprint import SchemaBlueprint, SchemaIdent, Grant, ObjectType, build_role_ident
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
        "owner_schema_read": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "owner_schema_write": {
            "type": "array",
            "items": {
                "type": "string"
            }
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
                    "is_sandbox": database_params.get('is_sandbox', False) or schema_params.get('is_sandbox', False),
                }

                owner_additional_grants = []

                for full_schema_name in schema_params.get('owner_schema_read', []):
                    owner_additional_grants.append(self.build_schema_role_grant(full_schema_name, 'READ'))

                for full_schema_name in schema_params.get('owner_schema_write', []):
                    owner_additional_grants.append(self.build_schema_role_grant(full_schema_name, 'WRITE'))

                bp = SchemaBlueprint(
                    full_name=SchemaIdent(self.env_prefix, database_path.name, schema_path.name),
                    is_transient=combined_params.get('is_transient', False),
                    retention_time=combined_params.get('retention_time', None),
                    is_sandbox=combined_params.get('is_sandbox', False),
                    owner_additional_grants=owner_additional_grants,
                    comment=schema_params.get('comment', None),
                )

                self.config.add_blueprint(bp)

    def build_schema_role_grant(self, full_schema_name, grant_type):
        database, schema = full_schema_name.split('.')

        return Grant(
            privilege="USAGE",
            on=ObjectType.ROLE,
            name=build_role_ident(self.env_prefix, database, schema, grant_type, self.config.SCHEMA_ROLE_SUFFIX),
        )
