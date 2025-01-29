from snowddl.blueprint import (
    RowAccessPolicyBlueprint,
    Ident,
    SchemaObjectIdent,
    NameWithType,
    DataType,
    ObjectType,
    RowAccessPolicyReference,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
row_access_policy_json_schema = {
    "type": "object",
    "properties": {
        "arguments": {
            "type": "object",
            "additionalProperties": {
                "type": "string"
            }
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
    "required": ["arguments", "body"],
    "additionalProperties": False
}
# fmt: on


class RowAccessPolicyParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("row_access_policy", row_access_policy_json_schema, self.process_row_access_policy)

    def process_row_access_policy(self, f: ParsedFile):
        arguments = [NameWithType(name=Ident(k), type=DataType(t)) for k, t in f.params.get("arguments", {}).items()]
        references = []

        for a in f.params.get("references", []):
            ref = RowAccessPolicyReference(
                object_type=ObjectType[a["object_type"].upper()],
                object_name=build_schema_object_ident(self.env_prefix, a["object_name"], f.database, f.schema),
                columns=[Ident(c) for c in a["columns"]],
            )

            references.append(ref)

        bp = RowAccessPolicyBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            body=self.normalise_sql_text_param(f.params["body"]),
            arguments=arguments,
            references=references,
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
