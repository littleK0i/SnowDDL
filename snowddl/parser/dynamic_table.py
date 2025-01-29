from snowddl.blueprint import (
    AccountObjectIdent,
    DynamicTableBlueprint,
    SchemaObjectIdent,
    DynamicTableColumn,
    Ident,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


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
        self.parse_schema_object_files("dynamic_table", dynamic_table_json_schema, self.process_dynamic_table)

    def process_dynamic_table(self, f: ParsedFile):
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
            is_transient=f.params.get("is_transient", False),
            retention_time=f.params.get("retention_time"),
            depends_on=set(
                build_schema_object_ident(self.env_prefix, d, f.database, f.schema) for d in f.params.get("depends_on", [])
            ),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)

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
