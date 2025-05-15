from functools import partial

from snowddl.blueprint import DatabaseRoleBlueprint, DatabaseRoleIdent, IdentPattern, GrantPattern, ObjectType
from snowddl.parser.abc_parser import AbstractParser


# fmt: off
database_role_json_schema = {
    "type": "object",
    "additionalProperties": {
        "properties": {
            "grants": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1
                }
            },
            "comment": {
                "type": "string"
            }
        },
        "required": ["grants"],
        "additionalProperties": False
    }
}
# fmt: on


class DatabaseRoleParser(AbstractParser):
    def load_blueprints(self):
        for database_name in self.get_database_names():
            self.parse_multi_entity_file(
                f"{database_name}/database_role",
                database_role_json_schema,
                partial(self.process_database_role, database_name=database_name),
            )

    def process_database_role(self, role_name, role_params, database_name):
        bp = DatabaseRoleBlueprint(
            full_name=DatabaseRoleIdent(self.env_prefix, database_name, role_name),
            grant_patterns=self.get_grant_patterns(role_params),
            comment=role_params.get("comment"),
        )

        self.config.add_blueprint(bp)

    def get_grant_patterns(self, role_params):
        grant_patterns = []

        for definition, pattern_list in role_params["grants"].items():
            on, privileges = definition.upper().split(":")

            for p in privileges.split(","):
                for pattern in pattern_list:
                    grant_patterns.append(GrantPattern(privilege=p, on=ObjectType[on], pattern=IdentPattern(pattern)))

        return grant_patterns
