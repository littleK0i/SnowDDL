from snowddl.blueprint import AccountParameterBlueprint, Ident
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
account_params_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": ["boolean", "number", "string"]
    }
}
# fmt: on


class AccountParameterParser(AbstractParser):
    def load_blueprints(self):
        self.parse_single_entity_file("account_params", account_params_json_schema, self.process_account_params)

    def process_account_params(self, f: ParsedFile):
        for name, value in f.params.items():
            bp = AccountParameterBlueprint(
                full_name=Ident(name),
                value=value,
                comment=None,
            )

            if str(bp.full_name) == "NETWORK_POLICY":
                raise ValueError(
                    "NETWORK_POLICY in account_params.yaml is no longer supported. Please use account_policy.yaml instead. Read more: https://docs.snowddl.com/breaking-changes-log/0.33.0-october-2024"
                )

            self.config.add_blueprint(bp)
