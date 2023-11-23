from snowddl.blueprint import ExternalAccessIntegrationBlueprint, SchemaObjectIdent, AccountObjectIdent, Ident
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
external_access_integration_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "allowed_network_rules": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1
            },
            "allowed_api_authentication_integrations": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1
            },
            "allowed_authentication_secrets": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1
            },
            "enabled": {
                "type": "boolean"
            },
            "comment": {
                "type": "string"
            }
        },
        "required": ["allowed_network_rules"],
        "additionalProperties": False
    }
}
# fmt: on


class ExternalAccessIntegrationParser(AbstractParser):
    def load_blueprints(self):
        self.parse_single_file(
            self.base_path / "external_access_integration.yaml",
            external_access_integration_json_schema,
            self.process_external_access_integration,
        )

    def process_external_access_integration(self, file: ParsedFile):
        for integration_name, integration in file.params.items():
            allowed_network_rules = [
                SchemaObjectIdent(self.env_prefix, *network_rule.split("."))
                for network_rule in integration.get("allowed_network_rules")
            ]
            allowed_api_authentication_integrations = None
            allowed_authentication_secrets = None

            if integration.get("allowed_api_authentication_integrations"):
                allowed_api_authentication_integrations = [
                    Ident(api_integration) for api_integration in integration.get("allowed_api_authentication_integrations")
                ]

            if integration.get("allowed_authentication_secrets"):
                allowed_authentication_secrets = [
                    SchemaObjectIdent(self.env_prefix, *secret_name.split("."))
                    for secret_name in integration.get("allowed_authentication_secrets")
                ]

            bp = ExternalAccessIntegrationBlueprint(
                full_name=AccountObjectIdent(self.env_prefix, integration_name),
                allowed_network_rules=allowed_network_rules,
                allowed_api_authentication_integrations=allowed_api_authentication_integrations,
                allowed_authentication_secrets=allowed_authentication_secrets,
                enabled=integration.get("enabled", True),
                comment=integration.get("comment"),
            )

            self.config.add_blueprint(bp)
