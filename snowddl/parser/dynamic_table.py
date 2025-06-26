from functools import partial

from snowddl.blueprint import (
    AccountObjectIdent,
    DynamicTableBlueprint,
    SchemaObjectIdent,
    DynamicTableColumn,
    Ident,
    ObjectType,
    build_schema_object_ident,
    AggregationPolicyBlueprint,
    AggregationPolicyReference,
    MaskingPolicyBlueprint,
    MaskingPolicyReference,
    ProjectionPolicyBlueprint,
    ProjectionPolicyReference,
    RowAccessPolicyBlueprint,
    RowAccessPolicyReference,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile
from snowddl.parser.schema import database_json_schema, schema_json_schema


# fmt: off
dynamic_table_json_schema = {
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
        "target_lag": {
            "type": "string"
        },
        "warehouse": {
            "type": "string",
        },
        "refresh_mode": {
            "type": "string",
        },
        "initialize": {
            "type": "string",
        },
        "cluster_by": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "is_transient": {
            "type": "boolean"
        },
        "retention_time": {
            "type": "integer"
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
    "required": ["text", "target_lag", "warehouse"],
    "additionalProperties": False
}
# fmt: on


class DynamicTableParser(AbstractParser):
    unit_singular_to_plural = {
        "second": "seconds",
        "minute": "minutes",
        "hour": "hours",
        "day": "days",
    }

    unit_plural_to_singular = {v: k for k, v in unit_singular_to_plural.items()}

    def load_blueprints(self):
        combined_params = {}

        for database_name in self.get_database_names():
            database_params = self.parse_single_entity_file(f"{database_name}/params", database_json_schema)
            combined_params[database_name] = {}

            for schema_name in self.get_schema_names_in_database(database_name):
                schema_params = self.parse_single_entity_file(f"{database_name}/{schema_name}/params", schema_json_schema)

                combined_params[database_name][schema_name] = {
                    "is_transient": database_params.get("is_transient", False) or schema_params.get("is_transient", False),
                    "retention_time": schema_params.get("retention_time"),
                }

        self.parse_schema_object_files(
            "dynamic_table", dynamic_table_json_schema, partial(self.process_dynamic_table, combined_params=combined_params)
        )

    def process_dynamic_table(self, f: ParsedFile, combined_params: dict):
        column_blueprints = []

        for col_name, col_comment in f.params.get("columns", {}).items():
            column_blueprints.append(
                DynamicTableColumn(
                    name=Ident(col_name),
                    comment=col_comment if col_comment else None,
                )
            )

        bp = DynamicTableBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            text=self.normalise_sql_text_param(f.params["text"]),
            columns=column_blueprints if column_blueprints else None,
            target_lag=self.normalise_target_lag(f.params["target_lag"]),
            warehouse=AccountObjectIdent(self.env_prefix, f.params["warehouse"]),
            refresh_mode=f.params.get("refresh_mode").upper() if f.params.get("refresh_mode") else None,
            initialize=f.params.get("initialize").upper() if f.params.get("initialize") else None,
            cluster_by=f.params.get("cluster_by"),
            is_transient=f.params.get("is_transient", combined_params[f.database][f.schema].get("is_transient", False)),
            retention_time=f.params.get("retention_time", combined_params[f.database][f.schema].get("retention_time", None)),
            depends_on=set(
                build_schema_object_ident(self.env_prefix, d, f.database, f.schema) for d in f.params.get("depends_on", [])
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
                object_type=ObjectType.DYNAMIC_TABLE,
                object_name=bp.full_name,
                columns=[Ident(c) for c in f.params["aggregation_policy"].get("columns", [])],
            )

            self.config.add_policy_reference(AggregationPolicyBlueprint, policy_name, ref)

        for mp in f.params.get("masking_policies", []):
            policy_name = build_schema_object_ident(self.env_prefix, mp["policy_name"], f.database, f.schema)

            ref = MaskingPolicyReference(
                object_type=ObjectType.DYNAMIC_TABLE,
                object_name=bp.full_name,
                columns=[Ident(c) for c in mp["columns"]],
            )

            self.config.add_policy_reference(MaskingPolicyBlueprint, policy_name, ref)

        for pp in f.params.get("projection_policies", []):
            policy_name = build_schema_object_ident(self.env_prefix, pp["policy_name"], f.database, f.schema)

            ref = ProjectionPolicyReference(
                object_type=ObjectType.DYNAMIC_TABLE,
                object_name=bp.full_name,
                column=Ident(pp["column"]),
            )

            self.config.add_policy_reference(ProjectionPolicyBlueprint, policy_name, ref)

        if f.params.get("row_access_policy"):
            policy_name = build_schema_object_ident(
                self.env_prefix, f.params["row_access_policy"]["policy_name"], f.database, f.schema
            )

            ref = RowAccessPolicyReference(
                object_type=ObjectType.DYNAMIC_TABLE,
                object_name=bp.full_name,
                columns=[Ident(c) for c in f.params["row_access_policy"]["columns"]],
            )

            self.config.add_policy_reference(RowAccessPolicyBlueprint, policy_name, ref)

    def normalise_target_lag(self, target_lag: str):
        if target_lag.upper() == "DOWNSTREAM":
            return "DOWNSTREAM"

        num, _, unit = target_lag.partition(" ")

        num = int(num)
        unit = unit.lower()

        if num > 1 and (unit in self.unit_singular_to_plural):
            unit = self.unit_singular_to_plural[unit]
        elif num == 1 and (unit in self.unit_plural_to_singular):
            unit = self.unit_plural_to_singular[unit]

        return f"{num} {unit}"
