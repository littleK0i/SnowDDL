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
        path = self.base_path / "technical_role.yaml"

        if not path.exists():
            # Backwards compatibility with configs before "tech role" renaming
            path = self.base_path / "tech_role.yaml"

        self.parse_single_file(path, technical_role_json_schema, self.process_technical_role)

    def process_technical_role(self, f: ParsedFile):
        for technical_role_name, technical_role in f.params.items():
            technical_role_ident = build_role_ident(self.env_prefix, technical_role_name, self.config.TECHNICAL_ROLE_SUFFIX)

            grants = []
            account_grants = []

            for definition, pattern_list in technical_role.get("grants", {}).items():
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

            for privilege in technical_role.get("account_grants", []):
                account_grants.append(AccountGrant(privilege=privilege))

            bp = TechnicalRoleBlueprint(
                full_name=technical_role_ident,
                grants=grants,
                account_grants=account_grants,
                comment=technical_role.get("comment"),
            )

            self.config.add_blueprint(bp)
