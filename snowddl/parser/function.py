from snowddl.blueprint import FunctionBlueprint, Ident, IdentWithPrefix, ComplexIdentWithPrefixAndArgs, NameWithType, DataType
from snowddl.parser.abc_parser import AbstractParser


function_json_schema = {
    "type": "object",
    "properties": {
        "language": {
            "type": "string"
        },
        "arguments": {
            "type": "object",
            "additionalProperties": {
                "type": "string"
            }
        },
        "returns": {
            "anyOf": [
                {
                    "type": "string"
                },
                {
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                }
            ]
        },
        "body": {
            "type": "string"
        },
        "is_secure": {
            "type": "boolean"
        },
        "is_strict": {
            "type": "boolean"
        },
        "is_immutable": {
            "type": "boolean"
        },
        "comment": {
            "type": "string"
        }
    },
    "required": ["returns", "body"],
    "additionalProperties": False
}


class FunctionParser(AbstractParser):
    def load_blueprints(self):
        for f in self.parse_schema_object_files("function", function_json_schema):
            arguments = [NameWithType(name=Ident(k), type=DataType(t)) for k, t in f.params.get('arguments', {}).items()]

            if isinstance(f.params['returns'], dict):
                # Returns table
                returns = [NameWithType(name=Ident(k), type=DataType(t)) for k, t in f.params['returns'].items()]
            else:
                # Returns value
                returns = DataType(f.params['returns'])

            base_name = f.name[:f.name.index('(')]

            bp = FunctionBlueprint(
                full_name=ComplexIdentWithPrefixAndArgs(self.env_prefix, f.database, f.schema, base_name, data_types=[a.type.base_type for a in arguments]),
                database=IdentWithPrefix(self.env_prefix, f.database),
                schema=Ident(f.schema),
                name=Ident(base_name),
                language=f.params.get('language', 'SQL'),
                body=f.params['body'],
                arguments=arguments,
                returns=returns,
                is_secure=f.params.get('is_secure', False),
                is_strict=f.params.get('is_strict', False),
                is_immutable=f.params.get('is_immutable', False),
                comment=f.params.get('comment'),
            )

            self.config.add_blueprint(bp)
