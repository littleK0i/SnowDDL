from snowddl.blueprint import (
    JoinPolicyBlueprint,
    JoinPolicyReference,
    Ident,
    SchemaObjectIdent,
    ObjectType,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
join_policy_json_schema = {
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


class JoinPolicyParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("join_policy", join_policy_json_schema, self.process_join_policy)

    def process_join_policy(self, f: ParsedFile):
        references = []

        for r in f.params.get("references", []):
            ref = JoinPolicyReference(
                object_type=ObjectType[r["object_type"].upper()],
                object_name=build_schema_object_ident(self.env_prefix, r["object_name"], f.database, f.schema),
                columns=[Ident(c) for c in r["columns"]] if r.get("columns") else None,
            )

            references.append(ref)

        bp = JoinPolicyBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            body=self.normalise_sql_text_param(f.params["body"]),
            references=references,
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
