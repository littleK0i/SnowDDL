from snowddl.blueprint import GrantPattern, AccountGrant, TechnicalRoleBlueprint, ObjectType, IdentPattern, build_role_ident
from snowddl.parser.abc_parser import AbstractParser


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
        grant_patterns = []
        account_grants = []

        for definition, pattern_list in technical_role_params.get("grants", {}).items():
            on, privileges = definition.upper().split(":")

            for p in privileges.split(","):
                for pattern in pattern_list:
                    grant_patterns.append(GrantPattern(privilege=p, on=ObjectType[on], pattern=IdentPattern(pattern)))

        for privilege in technical_role_params.get("account_grants", []):
            account_grants.append(AccountGrant(privilege=privilege))

        bp = TechnicalRoleBlueprint(
            full_name=build_role_ident(self.env_prefix, technical_role_name, self.config.TECHNICAL_ROLE_SUFFIX),
            grant_patterns=grant_patterns,
            account_grants=account_grants,
            comment=technical_role_params.get("comment"),
        )

        self.config.add_blueprint(bp)
