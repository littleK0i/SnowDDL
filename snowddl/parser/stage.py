from snowddl.blueprint import StageBlueprint, Ident, IdentWithPrefix, ComplexIdentWithPrefix
from snowddl.parser.abc_parser import AbstractParser


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


class StageParser(AbstractParser):
    def load_blueprints(self):
        for f in self.parse_schema_object_files("stage", stage_json_schema):
            bp = StageBlueprint(
                full_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, f.name),
                database=IdentWithPrefix(self.env_prefix, f.database),
                schema=Ident(f.schema),
                name=Ident(f.name),
                url=f.params.get('url'),
                storage_integration=Ident(f.params['storage_integration']) if f.params.get('storage_integration') else None,
                encryption=self.normalise_params_dict(f.params.get('encryption')),
                directory=self.normalise_params_dict(f.params.get('directory')),
                file_format=self.config.build_complex_ident(f.params['file_format'], f.database, f.schema) if f.params.get('file_format') else None,
                copy_options=self.normalise_params_dict(f.params.get('copy_options')),
                comment=f.params.get('comment'),
            )

            self.config.add_blueprint(bp)
