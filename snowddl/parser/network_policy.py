from snowddl.blueprint import NetworkPolicyBlueprint, AccountObjectIdent
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
network_policy_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "allowed_ip_list": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1
            },
            "blocked_ip_list": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1
            },
            "comment": {
                "type": "string"
            }
        },
        "required": ["allowed_ip_list"],
        "additionalProperties": False
    }
}
# fmt: on


class NetworkPolicyParser(AbstractParser):
    def load_blueprints(self):
        self.parse_single_file(self.base_path / "network_policy.yaml", network_policy_json_schema, self.process_network_policy)

    def process_network_policy(self, file: ParsedFile):
        for policy_name, policy in file.params.items():
            bp = NetworkPolicyBlueprint(
                full_name=AccountObjectIdent(self.env_prefix, policy_name),
                allowed_ip_list=policy["allowed_ip_list"],
                blocked_ip_list=policy.get("blocked_ip_list", []),
                comment=policy.get("comment"),
            )

            self.config.add_blueprint(bp)
