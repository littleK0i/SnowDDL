from snowddl.blueprint import (
    StreamlitBlueprint,
    AccountObjectIdent,
    SchemaObjectIdent,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
streamlit_json_schema = {
    "type": "object",
    "properties": {
        "stage": {
            "type": "string"
        },
        "stage_directory": {
            "type": "string"
        },
        "main_file": {
            "type": "string"
        },
        "query_warehouse": {
            "type": "string"
        },
        "title": {
            "type": "string"
        },
        "comment": {
            "type": "string"
        },
        "external_access_integrations": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "secrets": {
            "type": "object",
            "additionalProperties": {
                "type": "string"
            }
        },
    },
    "required": ["stage"],
    "additionalProperties": False
}
# fmt: on


class StreamlitParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("streamlit", streamlit_json_schema, self.process_streamlit)

    def process_streamlit(self, f: ParsedFile):
        bp = StreamlitBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            stage=build_schema_object_ident(self.env_prefix, f.params["stage"], f.database, f.schema),
            stage_directory=f.params.get("stage_directory"),
            main_file=f.params.get("main_file", "streamlit_app.py"),
            query_warehouse=AccountObjectIdent(self.env_prefix, f.params["query_warehouse"]) if f.params.get("query_warehouse") else None,
            title=f.params.get("title"),
            comment=f.params.get("comment"),
            external_access_integrations=(
                [AccountObjectIdent(self.env_prefix, v) for v in f.params["external_access_integrations"]]
                if f.params.get("external_access_integrations")
                else None
            ),
            secrets=(
                {
                    k: build_schema_object_ident(self.env_prefix, v, f.database, f.schema)
                    for k, v in f.params["secrets"].items()
                }
                if f.params.get("secrets")
                else None
            ),
        )

        self.config.add_blueprint(bp)
