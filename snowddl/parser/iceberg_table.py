from functools import partial

from snowddl.blueprint import IcebergTableBlueprint, Ident, SchemaObjectIdent
from snowddl.parser.abc_parser import AbstractParser, ParsedFile
from snowddl.parser.schema import schema_json_schema


# fmt: off
iceberg_table_json_schema = {
    "type": "object",
    "properties": {
        "catalog_table_name": {
            "type": "string"
        },
        "catalog_namespace": {
            "type": "string",
        },
        "metadata_file_path": {
            "type": "string"
        },
        "base_location": {
            "type": "string"
        },
        "replace_invalid_characters": {
            "type": "boolean"
        },
        "auto_refresh": {
            "type": "boolean"
        },
        "comment": {
            "type": "string"
        },
    },
    "oneOf": [
        {"required": ["catalog_table_name"]},
        {"required": ["metadata_file_path"]},
        {"required": ["base_location"]},
    ],
    "additionalProperties": False
}
# fmt: on


class IcebergTableParser(AbstractParser):
    def load_blueprints(self):
        combined_params = {}

        for database_name in self.get_database_names():
            combined_params[database_name] = {}

            for schema_name in self.get_schema_names_in_database(database_name):
                schema_params = self.parse_single_entity_file(f"{database_name}/{schema_name}/params", schema_json_schema)
                combined_params[database_name][schema_name] = schema_params

        self.parse_schema_object_files(
            "iceberg_table", iceberg_table_json_schema, partial(self.process_table, combined_params=combined_params)
        )

    def process_table(self, f: ParsedFile, combined_params: dict):
        if not combined_params[f.database][f.schema].get("external_volume"):
            raise ValueError("Iceberg table requires parameter [external_volume] to be defined on schema level")

        if not combined_params[f.database][f.schema].get("catalog"):
            raise ValueError("Iceberg table requires parameter [catalog] to be defined on schema level")

        bp = IcebergTableBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            external_volume=Ident(combined_params[f.database][f.schema].get("external_volume")),
            catalog=Ident(combined_params[f.database][f.schema].get("catalog")),
            catalog_table_name=f.params.get("catalog_table_name"),
            catalog_namespace=f.params.get("catalog_namespace"),
            metadata_file_path=f.params.get("metadata_file_path"),
            base_location=f.params.get("base_location"),
            replace_invalid_characters=f.params.get("replace_invalid_characters", False),
            auto_refresh=f.params.get("auto_refresh", False),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
