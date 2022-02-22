from snowddl.blueprint import StreamBlueprint, Ident, IdentWithPrefix, ComplexIdentWithPrefix, ObjectType
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


stream_json_schema = {
    "type": "object",
    "properties": {
        "object_type": {
            "type": "string"
        },
        "object_name": {
            "type": "string"
        },
        "append_only": {
            "type": "boolean"
        },
        "insert_only": {
            "type": "boolean"
        },
        "show_initial_rows": {
            "type": "boolean"
        },
        "comment": {
            "type": "string"
        }
    },
    "required": ["object_type", "object_name"],
    "additionalProperties": False
}


class StreamParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("stream", stream_json_schema, self.process_stream)

    def process_stream(self, f: ParsedFile):
        bp = StreamBlueprint(
            full_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, f.name),
            database=IdentWithPrefix(self.env_prefix, f.database),
            schema=Ident(f.schema),
            name=Ident(f.name),
            object_type=ObjectType[f.params['object_type']],
            object_name=self.config.build_complex_ident(f.params['object_name'], f.database, f.schema),
            append_only=f.params.get('append_only'),
            insert_only=f.params.get('insert_only'),
            show_initial_rows=f.params.get('show_initial_rows'),
            comment=f.params.get('comment'),
        )

        self.config.add_blueprint(bp)
