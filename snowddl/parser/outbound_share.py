from snowddl.blueprint import AccountIdent, OutboundShareBlueprint, OutboundShareIdent, IdentPattern, GrantPattern, ObjectType
from snowddl.parser.abc_parser import AbstractParser


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
        self.parse_multi_entity_file("outbound_share", outbound_share_json_schema, self.process_outbound_share)

    def process_outbound_share(self, share_name, share_params):
        bp = OutboundShareBlueprint(
            full_name=OutboundShareIdent(self.env_prefix, share_name),
            accounts=self.get_share_accounts(share_params),
            share_restrictions=share_params.get("share_restrictions"),
            grant_patterns=self.get_share_grant_patterns(share_params),
            comment=share_params.get("comment"),
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

    def get_share_grant_patterns(self, share):
        grant_patterns = []

        for definition, pattern_list in share["grants"].items():
            on, privileges = definition.upper().split(":")

            for p in privileges.split(","):
                for pattern in pattern_list:
                    grant_patterns.append(GrantPattern(privilege=p, on=ObjectType[on], pattern=IdentPattern(pattern)))

        return grant_patterns
