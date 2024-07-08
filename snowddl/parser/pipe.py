from snowddl.blueprint import PipeBlueprint, Ident, SchemaObjectIdent, build_schema_object_ident
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
pipe_json_schema = {
    "type": "object",
    "properties": {
        "copy": {
            "type": "object",
            "properties": {
                "table": {
                    "type": "string"
                },
                "stage": {
                    "type": "string"
                },
                "path": {
                    "type": "string"
                },
                "pattern": {
                    "type": "string"
                },
                "file_format": {
                    "type": "string"
                },
                "match_by_column_name": {
                    "type": "string"
                },
                "include_metadata": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "transform": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "options": {
                    "type": "object",
                    "additionalProperties": {
                        "type": ["array", "boolean", "number", "string"]
                    }
                }
            },
            "required": ["table", "stage"],
            "additionalProperties": False
        },
        "auto_ingest": {
            "type": "boolean"
        },
        "aws_sns_topic": {
            "type": "string"
        },
        "integration": {
            "type": "string"
        },
        "error_integration": {
            "type": "string"
        },
        "comment": {
            "type": "string"
        }
    },
    "required": ["copy", "auto_ingest"],
    "additionalProperties": False
}
# fmt: on


class PipeParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("pipe", pipe_json_schema, self.process_pipe)

    def process_pipe(self, f: ParsedFile):
        file_format = None
        include_metadata = None

        copy = f.params["copy"]

        if copy.get("file_format"):
            file_format = build_schema_object_ident(self.env_prefix, copy.get("file_format"), f.database, f.schema)

        if copy.get("include_metadata"):
            include_metadata = {Ident(k): Ident(v) for k, v in copy.get("include_metadata").items()}

        bp = PipeBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            auto_ingest=f.params["auto_ingest"],
            copy_table_name=build_schema_object_ident(self.env_prefix, copy["table"], f.database, f.schema),
            copy_stage_name=build_schema_object_ident(self.env_prefix, copy["stage"], f.database, f.schema),
            copy_path=copy.get("path"),
            copy_pattern=copy.get("pattern"),
            copy_transform=self.normalise_params_dict(copy.get("transform")),
            copy_file_format=file_format,
            copy_match_by_column_name=copy.get("match_by_column_name"),
            copy_include_metadata=include_metadata,
            copy_options=self.normalise_params_dict(copy.get("options")),
            aws_sns_topic=f.params.get("aws_sns_topic"),
            integration=Ident(f.params["integration"]) if f.params.get("integration") else None,
            error_integration=Ident(f.params["error_integration"]) if f.params.get("error_integration") else None,
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
