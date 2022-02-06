from snowddl.blueprint import NetworkPolicyBlueprint, Ident
from snowddl.parser.abc_parser import AbstractParser


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


class NetworkPolicyParser(AbstractParser):
    def load_blueprints(self):
        network_policy_config = self.parse_single_file(self.base_path / 'network_policy.yaml', network_policy_json_schema)

        for policy_name, policy in network_policy_config.items():
            bp = NetworkPolicyBlueprint(
                full_name=Ident(policy_name),
                allowed_ip_list=policy['allowed_ip_list'],
                blocked_ip_list=policy.get('blocked_ip_list', []),
                comment=policy.get('comment'),
            )

            self.config.add_blueprint(bp)
