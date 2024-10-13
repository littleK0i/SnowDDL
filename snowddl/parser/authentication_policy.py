from snowddl.blueprint import AuthenticationPolicyBlueprint, SchemaObjectIdent
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
authentication_policy_json_schema = {
    "type": "object",
    "properties": {
        "authentication_methods": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "mfa_authentication_methods": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "mfa_enrollment": {
            "type": "string"
        },
        "client_types": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "security_integrations": {
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
# fmt: on


class AuthenticationPolicyParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files(
            "authentication_policy", authentication_policy_json_schema, self.process_authentication_policy
        )

    def process_authentication_policy(self, f: ParsedFile):
        # As of Oct 2024, no easy way around hardcoding defaults
        # Cannot distinguish missing value and explicitly set default value
        # https://docs.snowflake.com/en/sql-reference/sql/create-authentication-policy
        bp = AuthenticationPolicyBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            authentication_methods=self.normalise_params_list(f.params.get("authentication_methods"))
            if f.params.get("authentication_methods")
            else ["ALL"],
            mfa_authentication_methods=self.normalise_params_list(f.params.get("mfa_authentication_methods"))
            if f.params.get("mfa_authentication_methods")
            else ["PASSWORD", "SAML"],
            mfa_enrollment=f.params.get("mfa_enrollment").upper() if f.params.get("mfa_enrollment") else "OPTIONAL",
            client_types=self.normalise_params_list(f.params.get("client_types")) if f.params.get("client_types") else ["ALL"],
            security_integrations=self.normalise_params_list(f.params.get("security_integrations"))
            if f.params.get("security_integrations")
            else ["ALL"],
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
