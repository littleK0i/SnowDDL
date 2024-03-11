from snowddl.blueprint import AccountObjectIdent, DynamicTableBlueprint, SchemaObjectIdent, build_schema_object_ident
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
dynamic_table_json_schema = {
    "type": "object",
    "properties": {
        "text": {
            "type": "string"
        },
        "target_lag": {
            "type": "string"
        },
        "warehouse": {
            "type": "string",
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
        bp = DynamicTableBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            text=f.params["text"],
            target_lag=self.normalize_target_lag(f.params["target_lag"]),
            warehouse=AccountObjectIdent(self.env_prefix, f.params["warehouse"]),
            depends_on=set(
                build_schema_object_ident(self.env_prefix, d, f.database, f.schema) for d in f.params.get("depends_on", [])
            ),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)

    def normalize_target_lag(self, target_lag: str):
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
