from re import compile, IGNORECASE

from snowddl.blueprint import (
    ExternalTableBlueprint,
    ExternalTableColumn,
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
external_table_json_schema = table_json_schema = {
    "type": "object",
    "properties": {
        "columns": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string"
                    },
                    "expr": {
                        "type": "string"
                    },
                    "comment": {
                        "type": "string"
                    }
                },
                "required": ["type", "expr"],
                "additionalProperties": False
            }
        },
        "location": {
            "type": "object",
            "properties": {
                "stage": {
                    "type": "string"
                },
                "path": {
                    "type": "string"
                },
                "pattern": {
                    "type": "string"
                },
                "file_format": {
                    "type": "string"
                }
            },
            "required": ["stage", "file_format"],
            "additionalProperties": False
        },
        "partition_by": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "partition_type": {
            "type": "string",
            "pattern": "^[A-Za-z_]+$"
        },
        "auto_refresh": {
            "type": "boolean"
        },
        "refresh_on_create": {
            "type": "boolean"
        },
        "aws_sns_topic": {
            "type": "string"
        },
        "table_format": {
            "type": "string",
            "pattern": "^[A-Za-z_]+$"
        },
        "integration": {
            "type": "string"
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
        }
    },
    "required": ["location"],
    "additionalProperties": False
}
# fmt: on


class ExternalTableParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("external_table", external_table_json_schema, self.process_external_table)

    def process_external_table(self, f: ParsedFile):
        column_blueprints = []

        for col_name, col in f.params["columns"].items():
            m = col_type_re.match(col["type"])

            if not m:
                raise ValueError(
                    f"Incorrect short syntax for column [{col_name}] in table [{f.database}.{f.schema}.{f.name}]: {col['type']}"
                )

            column_blueprints.append(
                ExternalTableColumn(
                    name=Ident(col_name),
                    type=DataType(m.group("type")),
                    expr=col["expr"],
                    not_null=bool(m.group("not_null")),
                    comment=col.get("comment"),
                )
            )

        bp = ExternalTableBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            columns=column_blueprints if column_blueprints else None,
            partition_by=[Ident(col_name) for col_name in f.params["partition_by"]] if f.params.get("partition_by") else None,
            partition_type=f.params["partition_type"].upper() if f.params.get("partition_type") else None,
            location_stage=build_schema_object_ident(self.env_prefix, f.params["location"]["stage"], f.database, f.schema),
            location_path=f.params["location"].get("path"),
            location_pattern=f.params["location"].get("pattern"),
            file_format=build_schema_object_ident(self.env_prefix, f.params["location"].get("file_format"), f.database, f.schema)
            if f.params["location"].get("file_format")
            else None,
            refresh_on_create=f.params.get("refresh_on_create", False),
            auto_refresh=f.params.get("auto_refresh", False),
            aws_sns_topic=f.params.get("aws_sns_topic"),
            table_format=f.params["table_format"].upper() if f.params.get("table_format") else None,
            integration=Ident(f.params["integration"]) if f.params.get("integration") else None,
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)

        # Constraints

        if f.params.get("primary_key"):
            bp = PrimaryKeyBlueprint(
                full_name=TableConstraintIdent(
                    self.env_prefix, f.database, f.schema, f.name, columns=[Ident(c) for c in f.params["primary_key"]]
                ),
                table_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
                columns=[Ident(c) for c in f.params["primary_key"]],
                comment=None,
            )

            self.config.add_blueprint(bp)

        for columns in f.params.get("unique_keys", []):
            bp = UniqueKeyBlueprint(
                full_name=TableConstraintIdent(
                    self.env_prefix, f.database, f.schema, f.name, columns=[Ident(c) for c in columns]
                ),
                table_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
                columns=[Ident(c) for c in columns],
                comment=None,
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
                comment=None,
            )

            self.config.add_blueprint(bp)
