from snowddl.blueprint import Grant, AccountGrant, TechnicalRoleBlueprint, ObjectType, build_role_ident
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
technical_role_json_schema = {
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
            "account_grants": {
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
}
# fmt: on


class TechnicalRoleParser(AbstractParser):
    def load_blueprints(self):
        # Current config name
        self.parse_multi_entity_file("technical_role", technical_role_json_schema, self.process_technical_role)

        # Backwards compatible name
        self.parse_multi_entity_file("tech_role", technical_role_json_schema, self.process_technical_role)

    def process_technical_role(self, technical_role_name, technical_role_params):
        grants = []
        account_grants = []

        for definition, pattern_list in technical_role_params.get("grants", {}).items():
            on, privileges = definition.upper().split(":")

            for p in privileges.split(","):
                for pattern in pattern_list:
                    blueprints = self.config.get_blueprints_by_type_and_pattern(ObjectType[on].blueprint_cls, pattern)

                    if not blueprints:
                        raise ValueError(f"No {ObjectType[on].plural} matched wildcard grant with pattern [{pattern}]")

                    for object_bp in blueprints.values():
                        grants.append(
                            Grant(
                                privilege=p,
                                on=ObjectType[on],
                                name=object_bp.full_name,
                            )
                        )

        for privilege in technical_role_params.get("account_grants", []):
            account_grants.append(AccountGrant(privilege=privilege))

        bp = TechnicalRoleBlueprint(
            full_name=build_role_ident(self.env_prefix, technical_role_name, self.config.TECHNICAL_ROLE_SUFFIX),
            grants=grants,
            account_grants=account_grants,
            comment=technical_role_params.get("comment"),
        )

        self.config.add_blueprint(bp)
