from functools import partial
from re import compile, IGNORECASE
from typing import Dict, List, Union

from snowddl.blueprint import (
    TableBlueprint,
    TableColumn,
    PrimaryKeyBlueprint,
    UniqueKeyBlueprint,
    ForeignKeyBlueprint,
    DataType,
    Ident,
    SchemaObjectIdent,
    TableConstraintIdent,
    build_schema_object_ident,
    SearchOptimizationItem,
    ObjectType,
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

col_type_re = compile(r"^(?P<type>[a-z0-9_]+(\((\d+|int|float)(,(\d+))?\))?)" r"(?P<not_null> NOT NULL)?$", IGNORECASE)


# fmt: off
table_json_schema = {
    "type": "object",
    "properties": {
        "columns": {
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
                            "default_sequence": {
                                "type": "string"
                            },
                            "expression": {
                                "type": "string"
                            },
                            "collate": {
                                "type": "string"
                            },
                            "comment": {
                                "type": "string"
                            }
                        },
                        "required": ["type"],
                        "additionalProperties": False
                    }
                ]
            }
        },
        "cluster_by": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "change_tracking": {
            "type": "boolean"
        },
        "search_optimization": {
            "anyOf": [
                {
                    "type": "boolean"
                },
                {
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "minItems": 1,
                        }
                    }
                }
            ]
        },
        "comment": {
            "type": "string"
        },
        "primary_key": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "unique_keys": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
            }
        },
        "foreign_keys": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "columns": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    },
                    "ref_table": {
                        "type": "string"
                    },
                    "ref_columns": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    }
                },
                "additionalProperties": False
            },
            "minItems": 1
        },
        "is_transient": {
            "type": "boolean"
        },
        "retention_time": {
            "type": "integer"
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
    "additionalProperties": False
}
# fmt: on


class TableParser(AbstractParser):
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

        self.parse_schema_object_files("table", table_json_schema, partial(self.process_table, combined_params=combined_params))

    def process_table(self, f: ParsedFile, combined_params: dict):
        column_blueprints = []

        for col_name, col in f.params["columns"].items():
            # Short syntax
            if isinstance(col, str):
                col = {"type": col}

            m = col_type_re.match(col["type"])

            if not m:
                raise ValueError(
                    f"Incorrect short syntax for column [{col_name}] in table [{f.database}.{f.schema}.{f.name}]: {col['type']}"
                )

            # Default for sequence
            if col.get("default_sequence"):
                col_default = build_schema_object_ident(self.env_prefix, col["default_sequence"], f.database, f.schema)
            else:
                col_default = col.get("default")

            column_blueprints.append(
                TableColumn(
                    name=Ident(col_name),
                    type=DataType(m.group("type")),
                    not_null=bool(m.group("not_null")),
                    default=col_default,
                    expression=col.get("expression"),
                    collate=col.get("collate").lower() if col.get("collate") else None,
                    comment=col.get("comment"),
                )
            )

        bp = TableBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            columns=column_blueprints,
            cluster_by=f.params.get("cluster_by", None),
            is_transient=f.params.get("is_transient", combined_params[f.database][f.schema].get("is_transient", False)),
            retention_time=f.params.get("retention_time", combined_params[f.database][f.schema].get("retention_time", None)),
            change_tracking=f.params.get("change_tracking", False),
            search_optimization=self.get_search_optimization(f.params.get("search_optimization", False)),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)

        # Constraints

        if f.params.get("primary_key"):
            key_bp = PrimaryKeyBlueprint(
                full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
                table_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
                columns=[Ident(c) for c in f.params.get("primary_key")],
                comment=None,
            )

            self.config.add_blueprint(key_bp)

        for columns in f.params.get("unique_keys", []):
            key_bp = UniqueKeyBlueprint(
                full_name=TableConstraintIdent(
                    self.env_prefix, f.database, f.schema, f.name, columns=[Ident(c) for c in columns]
                ),
                table_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
                columns=[Ident(c) for c in columns],
                comment=None,
            )

            self.config.add_blueprint(key_bp)

        for fk in f.params.get("foreign_keys", []):
            key_bp = ForeignKeyBlueprint(
                full_name=TableConstraintIdent(
                    self.env_prefix, f.database, f.schema, f.name, columns=[Ident(c) for c in fk["columns"]]
                ),
                table_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
                columns=[Ident(c) for c in fk["columns"]],
                ref_table_name=build_schema_object_ident(self.env_prefix, fk["ref_table"], f.database, f.schema),
                ref_columns=[Ident(c) for c in fk["ref_columns"]],
                comment=None,
            )

            self.config.add_blueprint(key_bp)

        # Policies

        if f.params.get("aggregation_policy"):
            policy_name = build_schema_object_ident(
                self.env_prefix, f.params["aggregation_policy"]["policy_name"], f.database, f.schema
            )

            ref = AggregationPolicyReference(
                object_type=ObjectType.TABLE,
                object_name=bp.full_name,
                columns=[Ident(c) for c in f.params["aggregation_policy"].get("columns", [])],
            )

            self.config.add_policy_reference(AggregationPolicyBlueprint, policy_name, ref)

        for mp in f.params.get("masking_policies", []):
            policy_name = build_schema_object_ident(self.env_prefix, mp["policy_name"], f.database, f.schema)

            ref = MaskingPolicyReference(
                object_type=ObjectType.TABLE,
                object_name=bp.full_name,
                columns=[Ident(c) for c in mp["columns"]],
            )

            self.config.add_policy_reference(MaskingPolicyBlueprint, policy_name, ref)

        for pp in f.params.get("projection_policies", []):
            policy_name = build_schema_object_ident(self.env_prefix, pp["policy_name"], f.database, f.schema)

            ref = ProjectionPolicyReference(
                object_type=ObjectType.TABLE,
                object_name=bp.full_name,
                column=Ident(pp["column"]),
            )

            self.config.add_policy_reference(ProjectionPolicyBlueprint, policy_name, ref)

        if f.params.get("row_access_policy"):
            policy_name = build_schema_object_ident(
                self.env_prefix, f.params["row_access_policy"]["policy_name"], f.database, f.schema
            )

            ref = RowAccessPolicyReference(
                object_type=ObjectType.TABLE,
                object_name=bp.full_name,
                columns=[Ident(c) for c in f.params["row_access_policy"]["columns"]],
            )

            self.config.add_policy_reference(RowAccessPolicyBlueprint, policy_name, ref)

    def get_search_optimization(self, search_optimization: Union[Dict[str, List[str]], bool]):
        # Legacy search optimization on the whole table
        if isinstance(search_optimization, bool):
            return search_optimization

        items = []

        # Detailed search optimization on specific columns
        for method, targets in search_optimization.items():
            for t in targets:
                t_parts = t.split(":", 2)

                items.append(
                    SearchOptimizationItem(
                        method=str(method).upper(),
                        target=Ident(t_parts[0]),
                    )
                )

        return items
