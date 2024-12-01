from snowddl.blueprint import (
    AccountObjectIdent,
    AuthenticationPolicyBlueprint,
    AuthenticationPolicyReference,
    NetworkPolicyBlueprint,
    NetworkPolicyReference,
    ObjectType,
    SchemaObjectIdent,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
account_policy_json_schema = {
    "type": "object",
    "properties": {
        "authentication_policy": {
            "type": "string"
        },
        "network_policy": {
            "type": "string"
        },
    },
    "additionalProperties": False
}
# fmt: on


class AccountPolicyParser(AbstractParser):
    def load_blueprints(self):
        self.parse_single_entity_file("account_policy", account_policy_json_schema, self.process_account_policy)

    def process_account_policy(self, f: ParsedFile):
        if self.env_prefix:
            # Account-level policies are ignored with env_prefix is present
            # Can only assign one account-level policy per account, no way around it
            return

        if f.params.get("authentication_policy"):
            policy_name_parts = f.params.get("authentication_policy").split(".")

            if len(policy_name_parts) != 3:
                raise ValueError(
                    f"Authentication policy [{f.params.get('authentication_policy')}] should use fully-qualified identifier <database>.<schema>.<name>"
                )

            policy_name = SchemaObjectIdent(self.env_prefix, *policy_name_parts)

            ref = AuthenticationPolicyReference(
                object_type=ObjectType.ACCOUNT,
            )

            self.config.add_policy_reference(AuthenticationPolicyBlueprint, policy_name, ref)

        if f.params.get("network_policy"):
            policy_name = AccountObjectIdent(self.env_prefix, f.params.get("network_policy"))

            ref = NetworkPolicyReference(
                object_type=ObjectType.ACCOUNT,
            )

            self.config.add_policy_reference(NetworkPolicyBlueprint, policy_name, ref)
