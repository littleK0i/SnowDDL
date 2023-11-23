from snowddl.blueprint import SecretBlueprint, SchemaObjectIdent, Ident
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
secret_json_schema = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string"
        },
        "api_authentication": {
            "type": "string"
        },
        "oauth_scopes": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "oauth_refresh_token": {
            "type": "string"
        },
        "oauth_refresh_token_expiry_time": {
            "type": "string"
        },
        "username": {
            "type": "string"
        },
        "password": {
            "type": "string"
        },
        "secret_string": {
            "type": "string"
        },
        "comment": {
            "type": "string"
        },
    },
    "required": ["type"],
    "additionalProperties": False
}
# fmt: on


class SecretParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("secret", secret_json_schema, self.process_sequence)

    def process_sequence(self, f: ParsedFile):
        bp = SecretBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            type=str(f.params["type"]).upper(),
            api_authentication=Ident(f.params.get("api_authentication")) if f.params.get("api_authentication") else None,
            oauth_scopes=f.params.get("oauth_scopes"),
            oauth_refresh_token=f.params.get("oauth_refresh_token"),
            oauth_refresh_token_expiry_time=f.params.get("oauth_refresh_token_expiry_time"),
            username=f.params.get("username"),
            password=f.params.get("password"),
            secret_string=f.params.get("secret_string"),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
