from snowddl.blueprint import (
    ExternalFunctionBlueprint,
    Ident,
    SchemaObjectIdentWithArgs,
    NameWithType,
    DataType,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
external_function_json_schema = {
    "type": "object",
    "properties": {
        "arguments": {
            "type": "object",
            "additionalProperties": {
                "type": "string"
            }
        },
        "returns": {
            "type": "string"
        },
        "api_integration": {
            "type": "string"
        },
        "url": {
            "type": "string",
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
        "headers": {
            "type": "object",
            "additionalProperties": {
                "type": "string"
            }
        },
        "context_headers": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "max_batch_rows": {
            "type": "integer"
        },
        "compression": {
            "type": "string"
        },
        "request_translator": {
            "type": "string"
        },
        "response_translator": {
            "type": "string"
        },
        "comment": {
            "type": "string"
        }
    },
    "required": ["api_integration", "url"],
    "additionalProperties": False
}
# fmt: on


class ExternalFunctionParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("external_function", external_function_json_schema, self.process_function)

    def process_function(self, f: ParsedFile):
        arguments = [NameWithType(name=Ident(k), type=DataType(t)) for k, t in f.params.get("arguments", {}).items()]
        returns = DataType(f.params["returns"])

        base_name = self.validate_name_with_args(f.path, arguments)

        bp = ExternalFunctionBlueprint(
            full_name=SchemaObjectIdentWithArgs(
                self.env_prefix, f.database, f.schema, base_name, [a.type.base_type for a in arguments]
            ),
            arguments=arguments,
            returns=returns,
            api_integration=Ident(f.params.get("api_integration")),
            url=f.params["url"],
            is_secure=f.params.get("is_secure", False),
            is_strict=f.params.get("is_strict", False),
            is_immutable=f.params.get("is_immutable", False),
            headers=f.params.get("headers"),
            context_headers=[Ident(h) for h in f.params.get("context_headers")] if f.params.get("context_headers") else None,
            max_batch_rows=f.params.get("max_batch_rows"),
            compression=f.params.get("compression"),
            request_translator=build_schema_object_ident(self.env_prefix, f.params["request_translator"], f.database, f.schema)
            if f.params.get("request_translator")
            else None,
            response_translator=build_schema_object_ident(self.env_prefix, f.params["response_translator"], f.database, f.schema)
            if f.params.get("response_translator")
            else None,
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
