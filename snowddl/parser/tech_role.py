from snowddl.blueprint import Grant, TechRoleBlueprint, ComplexIdentWithPrefix, ObjectType
from snowddl.parser.abc_parser import AbstractParser


tech_role_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "grants": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "comment": {
                        "type": "string"
                    }
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


class TechRoleParser(AbstractParser):
    def load_blueprints(self):
        tech_roles_config = self.parse_single_file(self.base_path / 'tech_role.yaml', tech_role_json_schema)

        for tech_role_name, tech_role in tech_roles_config.items():
            tech_role_ident = self.config.build_role_ident(tech_role_name, self.config.TECH_ROLE_SUFFIX)

            grants = []

            for definition, object_name_list in tech_role['grants'].items():
                on, privileges = definition.upper().split(':')

                for p in privileges.split(','):
                    for object_name in object_name_list:
                        grants.append(Grant(
                            privilege=p,
                            on=ObjectType[on],
                            name=self.config.build_complex_ident(object_name),
                        ))

            bp = TechRoleBlueprint(
                full_name=tech_role_ident,
                grants=grants,
                future_grants=[],
                comment=tech_role.get('comment'),
            )

            self.config.add_blueprint(bp)
