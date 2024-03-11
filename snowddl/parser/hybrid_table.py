from re import compile, IGNORECASE

from snowddl.blueprint import (
    HybridTableBlueprint,
    IndexReference,
    TableColumn,
    PrimaryKeyBlueprint,
    UniqueKeyBlueprint,
    ForeignKeyBlueprint,
    DataType,
    Ident,
    SchemaObjectIdent,
    TableConstraintIdent,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile

col_type_re = compile(r"^(?P<type>[a-z0-9_]+(\((\d+)(,(\d+))?\))?)" r"(?P<not_null> NOT NULL)?$", IGNORECASE)


# fmt: off
hybrid_table_json_schema = {
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
                "additionalProperties": False,
                "required": ["columns", "ref_table", "ref_columns"],
            },
            "minItems": 1
        },
        "indexes": {
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
                    "include": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    },
                },
                "additionalProperties": False,
                "required": ["columns"],
            },
            "minItems": 1
        },
    },
    "additionalProperties": False,
    "required": ["columns", "primary_key"],
}
# fmt: on


class HybridTableParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("hybrid_table", hybrid_table_json_schema, self.process_table)

    def process_table(self, f: ParsedFile):
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

        if f.params.get("indexes"):
            indexes = [
                IndexReference(
                    columns=[Ident(c) for c in idx["columns"]],
                    include=[Ident(c) for c in idx["include"]] if idx.get("include") else None,
                )
                for idx in f.params.get("indexes")
            ]
        else:
            indexes = None

        bp = HybridTableBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            columns=column_blueprints,
            indexes=indexes,
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)

        # Constraints

        if f.params.get("primary_key"):
            bp = PrimaryKeyBlueprint(
                full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
                table_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
                columns=[Ident(c) for c in f.params.get("primary_key")],
            )

            self.config.add_blueprint(bp)

        for columns in f.params.get("unique_keys", []):
            bp = UniqueKeyBlueprint(
                full_name=TableConstraintIdent(
                    self.env_prefix, f.database, f.schema, f.name, columns=[Ident(c) for c in columns]
                ),
                table_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
                columns=[Ident(c) for c in columns],
            )

            self.config.add_blueprint(bp)

        for fk in f.params.get("foreign_keys", []):
            bp = ForeignKeyBlueprint(
                full_name=TableConstraintIdent(
                    self.env_prefix, f.database, f.schema, f.name, columns=[Ident(c) for c in fk["columns"]]
                ),
                table_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
                columns=[Ident(c) for c in fk["columns"]],
                ref_table_name=build_schema_object_ident(self.env_prefix, fk["ref_table"], f.database, f.schema),
                ref_columns=[Ident(c) for c in fk["ref_columns"]],
            )

            self.config.add_blueprint(bp)
