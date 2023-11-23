from snowddl.blueprint import (
    FunctionBlueprint,
    AccountObjectIdent,
    Ident,
    SchemaObjectIdentWithArgs,
    ArgumentWithType,
    NameWithType,
    DataType,
    StageWithPath,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
function_json_schema = {
    "type": "object",
    "properties": {
        "language": {
            "type": "string"
        },
        "arguments": {
            "type": "object",
            "minItems": 1,
            "items": {
                "anyOf": [
                    {
                        "type": "string"
                    },
                    {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string"
                            },
                            "default": {
                                "type": "string"
                            },
                        },
                        "required": ["type"],
                        "additionalProperties": False
                    }
                ]
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
        "is_memoizable": {
            "type": "boolean"
        },
        "runtime_version": {
            "type": ["number", "string"]
        },
        "imports": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "stage": {
                        "type": "string"
                    },
                    "path": {
                        "type": "string"
                    }
                },
                "required": ["stage"],
                "additionalProperties": False
            },
            "minItems": 1
        },
        "packages": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "handler": {
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
            },
        },
        "comment": {
            "type": "string"
        }
    },
    "anyOf": [
        {
            "required": ["body", "returns"]
        },
        {
            "required": ["handler", "returns"]
        }
    ],
    "additionalProperties": False
}
# fmt: on


class FunctionParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("function", function_json_schema, self.process_function)

    def process_function(self, f: ParsedFile):
        arguments = self.get_arguments(f)
        base_name = self.validate_name_with_args(f.path, arguments)

        bp = FunctionBlueprint(
            full_name=SchemaObjectIdentWithArgs(
                self.env_prefix, f.database, f.schema, base_name, data_types=[a.type.base_type for a in arguments]
            ),
            language=f.params.get("language", "SQL"),
            body=f.params.get("body"),
            arguments=arguments,
            returns=self.get_returns(f),
            is_secure=f.params.get("is_secure", False),
            is_strict=f.params.get("is_strict", False),
            is_immutable=f.params.get("is_immutable", False),
            is_memoizable=f.params.get("is_memoizable", False),
            runtime_version=str(f.params.get("runtime_version")) if f.params.get("runtime_version") else None,
            imports=self.get_imports(f),
            packages=f.params.get("packages"),
            handler=f.params.get("handler"),
            external_access_integrations=self.get_external_access_integrations(f),
            secrets=self.get_secrets(f),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)

    def get_arguments(self, f: ParsedFile):
        arguments = []

        for arg_name, arg in f.params.get("arguments", {}).items():
            # Short syntax
            if isinstance(arg, str):
                arg = {"type": arg}

            arguments.append(
                ArgumentWithType(
                    name=Ident(arg_name),
                    type=DataType(arg["type"]),
                    default=str(arg["default"]) if "default" in arg else None,
                )
            )

        return arguments

    def get_returns(self, f: ParsedFile):
        if isinstance(f.params["returns"], dict):
            # Returns table
            return [NameWithType(name=Ident(k), type=DataType(t)) for k, t in f.params["returns"].items()]

        return DataType(f.params["returns"])

    def get_imports(self, f: ParsedFile):
        if f.params.get("imports"):
            return [
                StageWithPath(
                    stage_name=build_schema_object_ident(self.env_prefix, i["stage"], f.database, f.schema),
                    path=self.normalise_stage_path(i["path"]),
                )
                for i in f.params.get("imports")
            ]

        return None

    def get_external_access_integrations(self, f: ParsedFile):
        if f.params.get("external_access_integrations"):
            return [AccountObjectIdent(self.env_prefix, i) for i in f.params.get("external_access_integrations")]

        return None

    def get_secrets(self, f: ParsedFile):
        if f.params.get("secrets"):
            return {
                k: build_schema_object_ident(self.env_prefix, v, f.database, f.schema) for k, v in f.params.get("secrets").items()
            }

        return None
