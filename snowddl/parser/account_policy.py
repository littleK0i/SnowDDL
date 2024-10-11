from snowddl.blueprint import AccountObjectIdent, NetworkPolicyBlueprint, NetworkPolicyReference, ObjectType
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
account_policy_json_schema = {
    "type": "object",
    "properties": {
        "network_policy": {
            "type": "string"
        },
    },
    "additionalProperties": False
}
# fmt: on


class AccountPolicyParser(AbstractParser):
    def load_blueprints(self):
        self.parse_single_file(self.base_path / "account_policy.yaml", account_policy_json_schema, self.process_account_policy)

    def process_account_policy(self, f: ParsedFile):
        if self.env_prefix:
            # Account-level policies are ignored with env_prefix is present
            # Can only assign one account-level policy per account, no way around it
            return

        if f.params.get("network_policy"):
            policy_name = AccountObjectIdent(self.env_prefix, f.params.get("network_policy"))

            ref = NetworkPolicyReference(
                object_type=ObjectType.ACCOUNT,
            )

            self.config.add_policy_reference(NetworkPolicyBlueprint, policy_name, ref)
