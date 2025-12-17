from snowddl.blueprint import (
    DatabaseIdent,
    SchemaIdent,
    ObjectType,
    BackupSetBlueprint,
    SchemaObjectIdent,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
backup_set_json_schema = {
    "type": "object",
    "properties": {
        "object_type": {
            "type": "string"
        },
        "object_name": {
            "type": "string"
        },
        "backup_policy": {
            "type": "string"
        },
        "comment": {
            "type": "string"
        }
    },
    "required": ["object_type", "object_name"],
    "additionalProperties": False
}
# fmt: on


class BackupSetParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("backup_set", backup_set_json_schema, self.process_backup_set)

    def process_backup_set(self, f: ParsedFile):
        object_type = ObjectType[f.params["object_type"]]

        if object_type == ObjectType.DATABASE:
            object_name = DatabaseIdent(self.env_prefix, f.params["object_name"])
        elif object_type == ObjectType.SCHEMA:
            object_name = SchemaIdent(self.env_prefix, *f.params["object_name"].split(".", 2))
        else:
            object_name = build_schema_object_ident(self.env_prefix, f.params["object_name"], f.database, f.schema)

        bp = BackupSetBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            object_type=ObjectType[f.params["object_type"]],
            object_name=object_name,
            backup_policy=build_schema_object_ident(self.env_prefix, f.params["backup_policy"], f.database, f.schema) if f.params.get("backup_policy") else None,
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
