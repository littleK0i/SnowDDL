from snowddl.blueprint import (
    DatabaseIdent,
    SchemaIdent,
    ObjectType,
    SnapshotSetBlueprint,
    SchemaObjectIdent,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
snapshot_set_json_schema = {
    "type": "object",
    "properties": {
        "object_type": {
            "type": "string"
        },
        "object_name": {
            "type": "string"
        },
        "snapshot_policy": {
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


class SnapshotSetParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("snapshot_set", snapshot_set_json_schema, self.process_snapshot_set)

    def process_snapshot_set(self, f: ParsedFile):
        object_type = ObjectType[f.params["object_type"]]

        if object_type == ObjectType.DATABASE:
            object_name = DatabaseIdent(self.env_prefix, f.params["object_name"])
        elif object_type == ObjectType.SCHEMA:
            object_name = SchemaIdent(self.env_prefix, *f.params["object_name"].split(".", 2))
        else:
            object_name = build_schema_object_ident(self.env_prefix, f.params["object_name"], f.database, f.schema)

        bp = SnapshotSetBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            object_type=ObjectType[f.params["object_type"]],
            object_name=object_name,
            snapshot_policy=build_schema_object_ident(self.env_prefix, f.params["snapshot_policy"], f.database, f.schema) if f.params.get("snapshot_policy") else None,
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
