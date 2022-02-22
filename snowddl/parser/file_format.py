from snowddl.blueprint import FileFormatBlueprint, Ident, IdentWithPrefix, ComplexIdentWithPrefix
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


file_format_json_schema = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string"
        },
        "format_options": {
            "type": "object",
            "additionalProperties": {
                "type": ["array", "boolean", "number", "string"]
            }
        },
        "comment": {
            "type": "string"
        }
    },
    "required": ["type"],
    "additionalProperties": False
}


class FileFormatParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("file_format", file_format_json_schema, self.process_file_format)

    def process_file_format(self, f: ParsedFile):
        bp = FileFormatBlueprint(
            full_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, f.name),
            database=IdentWithPrefix(self.env_prefix, f.database),
            schema=Ident(f.schema),
            name=Ident(f.name),
            type=f.params['type'].upper(),
            format_options={option_name.upper(): option_value for option_name, option_value in f.params.get('format_options', {}).items()},
            comment=f.params.get('comment'),
        )

        self.config.add_blueprint(bp)
