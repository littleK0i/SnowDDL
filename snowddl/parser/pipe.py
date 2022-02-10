from snowddl.blueprint import PipeBlueprint, Ident, IdentWithPrefix, ComplexIdentWithPrefix
from snowddl.parser.abc_parser import AbstractParser


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
        "comment": {
            "type": "string"
        }
    },
    "required": ["copy", "auto_ingest"],
    "additionalProperties": False
}


class PipeParser(AbstractParser):
    def load_blueprints(self):
        for f in self.parse_schema_object_files("pipe", pipe_json_schema):
            copy = f.params['copy']

            bp = PipeBlueprint(
                full_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, f.name),
                database=IdentWithPrefix(self.env_prefix, f.database),
                schema=Ident(f.schema),
                name=Ident(f.name),
                auto_ingest=f.params['auto_ingest'],
                copy_table_name=self.config.build_complex_ident(copy['table'], f.database, f.schema),
                copy_stage_name=self.config.build_complex_ident(copy['stage'], f.database, f.schema),
                copy_path=copy.get('path'),
                copy_pattern=copy.get('pattern'),
                copy_transform=self.normalise_params_dict(copy.get('transform')),
                copy_file_format=self.config.build_complex_ident(copy.get('file_format'), f.database, f.schema) if copy.get('file_format') else None,
                copy_options=self.normalise_params_dict(copy.get('options')),
                aws_sns_topic=f.params.get('aws_sns_topic'),
                integration=Ident(f.params['integration']) if f.params.get('integration') else None,
                comment=f.params.get('comment'),
            )

            self.config.add_blueprint(bp)
