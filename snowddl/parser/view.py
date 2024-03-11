from snowddl.blueprint import ViewBlueprint, ViewColumn, Ident, SchemaObjectIdent, build_schema_object_ident
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
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
        "comment": {
            "type": "string"
        }
    },
    "required": ["text"],
    "additionalProperties": False
}
# fmt: on


class ViewParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("view", view_json_schema, self.process_view)

    def process_view(self, f: ParsedFile):
        column_blueprints = []

        for col_name, col_comment in f.params.get("columns", {}).items():
            column_blueprints.append(
                ViewColumn(
                    name=Ident(col_name),
                    comment=col_comment if col_comment else None,
                )
            )

        bp = ViewBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            text=f.params["text"],
            columns=column_blueprints if column_blueprints else None,
            is_secure=f.params.get("is_secure", False),
            depends_on=set(
                build_schema_object_ident(self.env_prefix, v, f.database, f.schema) for v in f.params.get("depends_on", [])
            ),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
