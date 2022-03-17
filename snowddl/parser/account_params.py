from snowddl.blueprint import AccountParameterBlueprint, Ident
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


account_params_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": ["boolean", "number", "string"]
    }
}


class AccountParameterParser(AbstractParser):
    def load_blueprints(self):
        self.parse_single_file(self.base_path / 'account_params.yaml', account_params_json_schema, self.process_account_params)

    def process_account_params(self, f: ParsedFile):
        for name, value in f.params.items():
            bp = AccountParameterBlueprint(
                full_name=Ident(name),
                value=value,
                comment=None,
            )

            self.config.add_blueprint(bp)
