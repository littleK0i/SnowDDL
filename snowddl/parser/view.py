from snowddl.blueprint import ViewBlueprint, ViewColumn, Ident, IdentWithPrefix, ComplexIdentWithPrefix
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


view_json_schema = {
    "type": "object",
    "properties": {
        "columns": {
            "type": "object",
            "additionalProperties": {
                "type": ["string", "null"]
            }
        },
        "text": {
            "type": "string"
        },
        "is_secure": {
            "type": "boolean"
        },
        "depends_on": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
    },
    "additionalParams": False
}


class ViewParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("view", view_json_schema, self.process_view)

    def process_view(self, f: ParsedFile):
        column_blueprints = []

        for col_name, col_comment in f.params.get('columns', {}).items():
            column_blueprints.append(
                ViewColumn(
                    name=Ident(col_name),
                    comment=col_comment if col_comment else None,
                )
            )

        bp = ViewBlueprint(
            full_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, f.name),
            database=IdentWithPrefix(self.env_prefix, f.database),
            schema=Ident(f.schema),
            name=Ident(f.name),
            text=f.params['text'],
            columns=column_blueprints if column_blueprints else None,
            is_secure=f.params.get('is_secure', False),
            depends_on=[self.config.build_complex_ident(v, f.database, f.schema) for v in f.params.get('depends_on', [])],
            comment=f.params.get('comment'),
        )

        self.config.add_blueprint(bp)
