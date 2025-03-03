from snowddl.blueprint import AlertBlueprint, AccountObjectIdent, SchemaObjectIdent
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
alert_json_schema = {
    "type": "object",
    "properties": {
        "warehouse": {
            "type": "string"
        },
        "schedule": {
            "type": "string"
        },
        "condition": {
            "type": "string"
        },
        "action": {
            "type": "string"
        },
        "comment": {
            "type": "string"
        },
    },
    "required": ["schedule", "condition", "action"],
    "additionalProperties": False,
}
# fmt: on


class AlertParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("alert", alert_json_schema, self.process_alert)

    def process_alert(self, f: ParsedFile):
        bp = AlertBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            warehouse=AccountObjectIdent(self.env_prefix, f.params["warehouse"]) if f.params.get("warehouse") else None,
            schedule=str(f.params["schedule"]).strip(),
            condition=str(f.params["condition"]).strip(),
            action=str(f.params["action"]).strip(),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
