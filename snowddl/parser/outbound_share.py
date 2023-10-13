from snowddl.blueprint import AccountIdent, OutboundShareBlueprint, OutboundShareIdent, Grant, ObjectType
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
outbound_share_json_schema = {
    "type": "object",
    "additionalProperties": {
        "properties": {
            "accounts": {
                "type": "array",
                "items": {
                    "type": "string"
                },
            },
            "share_restrictions": {
                "type": "boolean"
            },
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


class OutboundShareParser(AbstractParser):
    def load_blueprints(self):
        self.parse_single_file(self.base_path / "outbound_share.yaml", outbound_share_json_schema, self.process_inbound_share)

    def process_inbound_share(self, f: ParsedFile):
        for share_name, share in f.params.items():
            bp = OutboundShareBlueprint(
                full_name=OutboundShareIdent(self.env_prefix, share_name),
                accounts=self.get_share_accounts(share),
                share_restrictions=share.get("share_restrictions", False),
                grants=self.get_share_grants(share),
                comment=share.get("comment"),
            )

            self.config.add_blueprint(bp)

    def get_share_accounts(self, share):
        share_accounts = []

        for account in share.get("accounts", []):
            account_parts = account.split(".")

            if len(account_parts) != 2:
                raise ValueError(
                    f"Invalid outbound share account format [{account}], expected identifier with exactly 2 parts: <organization>.<account>"
                )

            share_accounts.append(AccountIdent(*account_parts))

        return share_accounts

    def get_share_grants(self, share):
        grants = []

        for definition, pattern_list in share["grants"].items():
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

        return grants
