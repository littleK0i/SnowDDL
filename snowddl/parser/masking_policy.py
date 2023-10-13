from snowddl.blueprint import (
    MaskingPolicyBlueprint,
    Ident,
    SchemaObjectIdent,
    NameWithType,
    DataType,
    MaskingPolicyReference,
    ObjectType,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
masking_policy_json_schema = {
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
        "body": {
            "type": "string"
        },
        "references": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string"
                    },
                    "object_name": {
                        "type": "string"
                    },
                    "columns": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    }
                },
                "required": ["object_type", "object_name", "columns"],
                "additionalProperties": False
            },
            "minItems": 1
        },
        "comment": {
            "type": "string"
        }
    },
    "required": ["arguments", "returns", "body"],
    "additionalProperties": False
}
# fmt: on


class MaskingPolicyParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("masking_policy", masking_policy_json_schema, self.process_masking_policy)

    def process_masking_policy(self, f: ParsedFile):
        arguments = [NameWithType(name=Ident(k), type=DataType(t)) for k, t in f.params.get("arguments", {}).items()]
        references = []

        for a in f.params.get("references", []):
            ref = MaskingPolicyReference(
                object_type=ObjectType[a["object_type"].upper()],
                object_name=build_schema_object_ident(self.env_prefix, a["object_name"], f.database, f.schema),
                columns=[Ident(c) for c in a["columns"]],
            )

            references.append(ref)

        bp = MaskingPolicyBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            body=f.params["body"],
            arguments=arguments,
            returns=DataType(f.params["returns"]),
            references=references,
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
