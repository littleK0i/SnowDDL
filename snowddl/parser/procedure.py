from snowddl.blueprint import ProcedureBlueprint, Ident, SchemaObjectIdentWithArgs, NameWithType, DataType
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


procedure_json_schema = {
    "type": "object",
    "properties": {
        "language": {
            "type": "string"
        },
        "body": {
            "type": "string"
        },
        "arguments": {
            "type": "object",
            "additionalProperties": {
                "type": "string"
            }
        },
        "returns": {
            "type": "string"
        },
        "is_strict": {
            "type": "boolean"
        },
        "is_execute_as_caller": {
            "type": "boolean"
        },
        "comment": {
            "type": "string"
        }
    },
    "required": ["body", "returns"],
    "additionalProperties": False
}


class ProcedureParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("procedure", procedure_json_schema, self.process_procedure)

    def process_procedure(self, f: ParsedFile):
        arguments = [NameWithType(name=Ident(k), type=DataType(t)) for k, t in f.params.get('arguments', {}).items()]
        base_name = self.validate_name_with_args(f.path, arguments)

        bp = ProcedureBlueprint(
            full_name=SchemaObjectIdentWithArgs(self.env_prefix, f.database, f.schema, base_name, [a.type.base_type for a in arguments]),
            language=f.params.get('language', 'SQL'),
            body=f.params['body'],
            arguments=arguments,
            returns=DataType(f.params['returns']),
            is_strict=f.params.get('is_strict', False),
            is_immutable=f.params.get('is_immutable', False),
            is_execute_as_caller=f.params.get('is_execute_as_caller', False),
            comment=f.params.get('comment'),
        )

        self.config.add_blueprint(bp)
