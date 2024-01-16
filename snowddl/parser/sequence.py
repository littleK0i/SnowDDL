from snowddl.blueprint import SequenceBlueprint, SchemaObjectIdent
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
sequence_json_schema = {
    "type": "object",
    "properties": {
        "start": {
            "type": "integer"
        },
        "interval": {
            "type": "integer"
        },
        "is_ordered": {
            "type": "boolean"
        },
        "comment": {
            "type": "string"
        }
    },
    "additionalProperties": False
}
# fmt: on


class SequenceParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("sequence", sequence_json_schema, self.process_sequence)

    def process_sequence(self, f: ParsedFile):
        bp = SequenceBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            start=f.params.get("start", 1),
            interval=f.params.get("interval", 1),
            is_ordered=f.params.get("is_ordered"),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
