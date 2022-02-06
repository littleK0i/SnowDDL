from snowddl.blueprint import AccountParameterBlueprint, Ident
from snowddl.parser.abc_parser import AbstractParser


account_params_json_schema = {
    "type": "object",
    "additionalParams": {
        "type": ["boolean", "number", "string"]
    }
}


class AccountParameterParser(AbstractParser):
    def load_blueprints(self):
        params = self.parse_single_file(self.base_path / 'account_params.yaml', account_params_json_schema)

        for name, value in params.items():
            bp = AccountParameterBlueprint(
                full_name=Ident(name),
                value=value,
                comment=None,
            )

            self.config.add_blueprint(bp)
