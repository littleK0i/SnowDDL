from snowddl.blueprint import AccountObjectIdent, NetworkPolicyBlueprint, SchemaObjectIdent
from snowddl.parser.abc_parser import AbstractParser


# fmt: off
network_policy_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "allowed_network_rule_list": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1
            },
            "blocked_network_rule_list": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1
            },
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
        "additionalProperties": False
    }
}
# fmt: on


class NetworkPolicyParser(AbstractParser):
    def load_blueprints(self):
        self.parse_multi_entity_file("network_policy", network_policy_json_schema, self.process_network_policy)

    def process_network_policy(self, policy_name, policy_params):
        policy_name_ident = AccountObjectIdent(self.env_prefix, policy_name)

        bp = NetworkPolicyBlueprint(
            full_name=policy_name_ident,
            # fmt: off
            allowed_network_rule_list=self.build_network_rule_list(policy_name_ident, policy_params.get("allowed_network_rule_list", [])),
            blocked_network_rule_list=self.build_network_rule_list(policy_name_ident, policy_params.get("blocked_network_rule_list", [])),
            # fmt: on
            allowed_ip_list=policy_params.get("allowed_ip_list", []),
            blocked_ip_list=policy_params.get("blocked_ip_list", []),
            comment=policy_params.get("comment"),
        )

        if (
            not bp.allowed_network_rule_list
            and not bp.blocked_network_rule_list
            and not bp.allowed_ip_list
            and not bp.blocked_ip_list
        ):
            raise ValueError(f"NETWORK POLICY [{bp.full_name}] must have at least one condition")

        self.config.add_blueprint(bp)

    def build_network_rule_list(self, policy_name_ident, network_rules):
        network_rule_idents = []

        for rule in network_rules:
            parts = rule.split(".")

            if len(parts) != 3:
                raise ValueError(
                    f"Network rule [{rule}] for network policy [{policy_name_ident}] should use fully-qualified identifier <database>.<schema>.<name>"
                )

            network_rule_idents.append(SchemaObjectIdent(self.env_prefix, *parts))

        return network_rule_idents
