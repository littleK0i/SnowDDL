from snowddl.blueprint import EventTableBlueprint, SchemaObjectIdent
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
event_table_json_schema = {
    "type": "object",
    "properties": {
        "change_tracking": {
            "type": "boolean"
        },
        "comment": {
            "type": "string"
        },
    },
    "additionalProperties": False
}
# fmt: on


class EventTableParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("event_table", event_table_json_schema, self.process_event_table)

    def process_event_table(self, f: ParsedFile):
        bp = EventTableBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            change_tracking=f.params.get("change_tracking", False),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
