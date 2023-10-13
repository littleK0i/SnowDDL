from snowddl.blueprint import (
    StageBlueprint,
    StageFileBlueprint,
    Ident,
    SchemaObjectIdent,
    StageFileIdent,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
stage_json_schema = {
    "type": "object",
    "properties": {
        "url": {
            "type": "string"
        },
        "storage_integration": {
            "type": "string"
        },
        "encryption": {
            "type": "object",
            "additionalProperties": {
                "type": ["boolean", "number", "string"]
            }
        },
        "directory": {
            "type": "object",
            "additionalProperties": {
                "type": ["boolean", "number", "string"]
            }
        },
        "file_format": {
            "type": "string"
        },
        "copy_options": {
            "type": "object",
            "additionalProperties": {
                "type": ["array", "boolean", "number", "string"]
            }
        },
        "comment": {
            "type": "string"
        }
    },
    "additionalProperties": False
}
# fmt: on


class StageParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("stage", stage_json_schema, self.process_stage)

    def process_stage(self, f: ParsedFile):
        stage_files_dir = f.path.parent / f.name

        if stage_files_dir.is_dir() and f.params.get("url"):
            raise ValueError("External stage cannot have managed stage files")

        # Stage
        bp = StageBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            url=f.params.get("url"),
            storage_integration=Ident(f.params["storage_integration"]) if f.params.get("storage_integration") else None,
            encryption=self.normalise_params_dict(f.params.get("encryption")),
            directory=self.normalise_params_dict(f.params.get("directory")),
            file_format=build_schema_object_ident(self.env_prefix, f.params["file_format"], f.database, f.schema)
            if f.params.get("file_format")
            else None,
            copy_options=self.normalise_params_dict(f.params.get("copy_options")),
            upload_stage_files=stage_files_dir.is_dir(),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)

        # Stage files
        if stage_files_dir.is_dir():
            for path in stage_files_dir.glob("**/*"):
                if not path.is_file():
                    continue

                stage_path = f"/{path.relative_to(stage_files_dir)}"

                bp = StageFileBlueprint(
                    full_name=StageFileIdent(self.env_prefix, f.database, f.schema, f.name, path=stage_path),
                    local_path=str(path),
                    stage_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
                    stage_path=stage_path,
                    comment=None,
                )

                self.config.add_blueprint(bp)
