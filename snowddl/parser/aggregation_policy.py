from snowddl.blueprint import (
    AggregationPolicyBlueprint,
    AggregationPolicyReference,
    Ident,
    ObjectType,
    SchemaObjectIdent,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
aggregation_policy_json_schema = {
    "type": "object",
    "properties": {
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
                "required": ["object_type", "object_name"],
                "additionalProperties": False
            },
            "minItems": 1
        },
        "comment": {
            "type": "string"
        }
    },
    "required": ["body"],
    "additionalProperties": False
}
# fmt: on


class AggregationPolicyParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("aggregation_policy", aggregation_policy_json_schema, self.process_aggregation_policy)

    def process_aggregation_policy(self, f: ParsedFile):
        references = []

        for a in f.params.get("references", []):
            ref = AggregationPolicyReference(
                object_type=ObjectType[a["object_type"].upper()],
                object_name=build_schema_object_ident(self.env_prefix, a["object_name"], f.database, f.schema),
                columns=[Ident(c) for c in a.get("columns", [])],
            )

            references.append(ref)

        bp = AggregationPolicyBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            body=f.params["body"],
            references=references,
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
