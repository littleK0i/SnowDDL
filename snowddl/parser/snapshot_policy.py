from snowddl.blueprint import SnapshotPolicyBlueprint, SchemaObjectIdent
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
snapshot_policy_json_schema = {
    "type": "object",
    "properties": {
        "schedule": {
            "type": "string"
        },
        "expire_after_days": {
            "type": "integer"
        },
        "comment": {
            "type": "string"
        }
    },
    "additionalProperties": False
}
# fmt: on


class SnapshotPolicyParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("snapshot_policy", snapshot_policy_json_schema, self.process_snapshot_policy)

    def process_snapshot_policy(self, f: ParsedFile):
        bp = SnapshotPolicyBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            schedule=f.params.get("schedule"),
            expire_after_days=f.params.get("expire_after_days"),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
