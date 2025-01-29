from snowddl.blueprint import (
    ViewBlueprint,
    ViewColumn,
    Ident,
    SchemaObjectIdent,
    ObjectType,
    AggregationPolicyBlueprint,
    AggregationPolicyReference,
    MaskingPolicyBlueprint,
    MaskingPolicyReference,
    ProjectionPolicyBlueprint,
    ProjectionPolicyReference,
    RowAccessPolicyBlueprint,
    RowAccessPolicyReference,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
view_json_schema = {
    "type": "object",
    "properties": {
        "columns": {
            "type": "object",
            "additionalProperties": {
                "type": ["string", "null"]
            }
        },
        "text": {
            "type": "string"
        },
        "is_secure": {
            "type": "boolean"
        },
        "change_tracking": {
            "type": "boolean"
        },
        "depends_on": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "comment": {
            "type": "string"
        },
        "aggregation_policy": {
            "type": "object",
            "properties": {
                "policy_name": {
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
            "required": ["policy_name"],
            "additionalProperties": False
        },
        "masking_policies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "policy_name": {
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
                "required": ["policy_name", "columns"],
                "additionalProperties": False
            },
            "minItems": 1
        },
        "projection_policies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "policy_name": {
                        "type": "string"
                    },
                    "column": {
                        "type": "string",
                    }
                },
                "required": ["policy_name", "column"],
                "additionalProperties": False
            },
            "minItems": 1
        },
        "row_access_policy": {
            "type": "object",
            "properties": {
                "policy_name": {
                    "type": "string"
                },
                "columns": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1
                },
            },
            "required": ["policy_name", "columns"],
            "additionalProperties": False
        },
    },
    "required": ["text"],
    "additionalProperties": False
}
# fmt: on


class ViewParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("view", view_json_schema, self.process_view)

    def process_view(self, f: ParsedFile):
        column_blueprints = []

        for col_name, col_comment in f.params.get("columns", {}).items():
            column_blueprints.append(
                ViewColumn(
                    name=Ident(col_name),
                    comment=col_comment if col_comment else None,
                )
            )

        bp = ViewBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            text=self.normalise_sql_text_param(f.params["text"]),
            columns=column_blueprints if column_blueprints else None,
            is_secure=f.params.get("is_secure", False),
            change_tracking=f.params.get("change_tracking", False),
            depends_on=set(
                build_schema_object_ident(self.env_prefix, v, f.database, f.schema) for v in f.params.get("depends_on", [])
            ),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)

        # Policies

        if f.params.get("aggregation_policy"):
            policy_name = build_schema_object_ident(
                self.env_prefix, f.params["aggregation_policy"]["policy_name"], f.database, f.schema
            )

            ref = AggregationPolicyReference(
                object_type=ObjectType.VIEW,
                object_name=bp.full_name,
                columns=[Ident(c) for c in f.params["aggregation_policy"].get("columns", [])],
            )

            self.config.add_policy_reference(AggregationPolicyBlueprint, policy_name, ref)

        for mp in f.params.get("masking_policies", []):
            policy_name = build_schema_object_ident(self.env_prefix, mp["policy_name"], f.database, f.schema)

            ref = MaskingPolicyReference(
                object_type=ObjectType.VIEW,
                object_name=bp.full_name,
                columns=[Ident(c) for c in mp["columns"]],
            )

            self.config.add_policy_reference(MaskingPolicyBlueprint, policy_name, ref)

        for pp in f.params.get("projection_policies", []):
            policy_name = build_schema_object_ident(self.env_prefix, pp["policy_name"], f.database, f.schema)

            ref = ProjectionPolicyReference(
                object_type=ObjectType.VIEW,
                object_name=bp.full_name,
                column=Ident(pp["column"]),
            )

            self.config.add_policy_reference(ProjectionPolicyBlueprint, policy_name, ref)

        if f.params.get("row_access_policy"):
            policy_name = build_schema_object_ident(
                self.env_prefix, f.params["row_access_policy"]["policy_name"], f.database, f.schema
            )

            ref = RowAccessPolicyReference(
                object_type=ObjectType.VIEW,
                object_name=bp.full_name,
                columns=[Ident(c) for c in f.params["row_access_policy"]["columns"]],
            )

            self.config.add_policy_reference(RowAccessPolicyBlueprint, policy_name, ref)
