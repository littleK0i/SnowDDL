from snowddl.blueprint import Grant, TechRoleBlueprint, ObjectType, build_role_ident
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


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


class TechRoleParser(AbstractParser):
    def load_blueprints(self):
        self.parse_single_file(self.base_path / 'tech_role.yaml', tech_role_json_schema, self.process_tech_role)

    def process_tech_role(self, f: ParsedFile):
        for tech_role_name, tech_role in f.params.items():
            tech_role_ident = build_role_ident(self.env_prefix, tech_role_name, self.config.TECH_ROLE_SUFFIX)

            grants = []

            for definition, pattern_list in tech_role['grants'].items():
                on, privileges = definition.upper().split(':')

                for p in privileges.split(','):
                    for pattern in pattern_list:
                        blueprints = self.config.get_blueprints_by_type_and_pattern(ObjectType[on].blueprint_cls, pattern)

                        if not blueprints:
                            raise ValueError(f"No {ObjectType[on].plural} matched wildcard grant with pattern [{pattern}]")

                        for object_bp in blueprints.values():
                            grants.append(Grant(
                                privilege=p,
                                on=ObjectType[on],
                                name=object_bp.full_name,
                            ))

            bp = TechRoleBlueprint(
                full_name=tech_role_ident,
                grants=grants,
                future_grants=[],
                comment=tech_role.get('comment'),
            )

            self.config.add_blueprint(bp)
