from snowddl.blueprint import BackupPolicyBlueprint, SchemaObjectIdent
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
backup_policy_json_schema = {
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


class BackupPolicyParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("backup_policy", backup_policy_json_schema, self.process_backup_policy)

    def process_backup_policy(self, f: ParsedFile):
        bp = BackupPolicyBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            schedule=f.params.get("schedule"),
            expire_after_days=f.params.get("expire_after_days"),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
