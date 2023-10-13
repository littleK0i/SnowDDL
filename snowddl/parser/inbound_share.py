from snowddl.blueprint import DatabaseIdent, DatabaseShareBlueprint, InboundShareIdent
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
inbound_share_json_schema = {
    "type": "object",
    "additionalProperties": {
        "properties": {
            "share_name": {
                "type": "string"
            },
            "comment": {
                "type": "string"
            }
        },
        "required": ["share_name"],
        "additionalProperties": False
    }
}
# fmt: on


class InboundShareParser(AbstractParser):
    def load_blueprints(self):
        self.parse_single_file(self.base_path / "inbound_share.yaml", inbound_share_json_schema, self.process_inbound_share)

    def process_inbound_share(self, f: ParsedFile):
        for database_name, share in f.params.items():
            share_name_parts = share["share_name"].split(".")

            if len(share_name_parts) != 3:
                raise ValueError(
                    f"Invalid inbound share name format [{share['share_name']}], expected identifier with exactly 3 parts: <organization>.<account>.<share>"
                )

            bp = DatabaseShareBlueprint(
                # Inbound shares do not support env_prefix
                full_name=DatabaseIdent("", database_name),
                share_name=InboundShareIdent(*share_name_parts),
                comment=share.get("comment"),
            )

            self.config.add_blueprint(bp)
