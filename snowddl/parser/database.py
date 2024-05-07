from snowddl.blueprint import DatabaseBlueprint, DatabaseIdent, Grant, AccountGrant, ObjectType, Ident, build_role_ident
from snowddl.parser.abc_parser import AbstractParser


# fmt: off
database_json_schema = {
    "type": "object",
    "properties": {
        "permission_model": {
            "type": "string",
        },
        "is_transient": {
            "type": "boolean"
        },
        "retention_time": {
            "type": "integer"
        },
        "is_sandbox": {
            "type": "boolean"
        },
        "owner_integration_usage": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "owner_warehouse_usage": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "owner_account_grants": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "owner_global_roles": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "comment": {
            "type": "string"
        }
    },
    "additionalProperties": False
}
# fmt: on


class DatabaseParser(AbstractParser):
    def load_blueprints(self):
        for database_path in self.base_path.iterdir():
            if not database_path.is_dir():
                continue

            # Skip special sub-directories
            if database_path.name.startswith("__"):
                continue

            database_params = self.parse_single_file(database_path / "params.yaml", database_json_schema)

            database_name = database_path.name.upper()
            database_permission_model = self.config.get_permission_model(
                database_params.get("permission_model", self.config.DEFAULT_PERMISSION_MODEL).upper()
            )

            if not database_permission_model.ruleset.create_database_owner_role:
                for k in database_params:
                    if k.startswith("owner_"):
                        raise ValueError(
                            f"Cannot use parameter [{k}] for database [{database_name}], it should be configured on schema level"
                        )

            owner_additional_grants = []
            owner_additional_account_grants = []

            for integration_name in database_params.get("owner_integration_usage", []):
                owner_additional_grants.append(self.build_integration_usage_grant(integration_name))

            for warehouse_name in database_params.get("owner_warehouse_usage", []):
                owner_additional_grants.append(self.build_warehouse_role_grant(warehouse_name, self.config.USAGE_ROLE_TYPE))

            for account_grant in database_params.get("owner_account_grants", []):
                owner_additional_account_grants.append(self.build_account_grant(account_grant))

            for global_role_name in database_params.get("owner_global_roles", []):
                owner_additional_grants.append(self.build_global_role_grant(global_role_name))

            bp = DatabaseBlueprint(
                full_name=DatabaseIdent(self.env_prefix, database_name),
                permission_model=database_permission_model,
                is_transient=database_params.get("is_transient", False),
                retention_time=database_params.get("retention_time", None),
                is_sandbox=database_params.get("is_sandbox", False),
                owner_additional_grants=owner_additional_grants,
                owner_additional_account_grants=owner_additional_account_grants,
                comment=database_params.get("comment", None),
            )

            self.config.add_blueprint(bp)

    def build_warehouse_role_grant(self, warehouse_name, role_type):
        return Grant(
            privilege="USAGE",
            on=ObjectType.ROLE,
            name=build_role_ident(self.env_prefix, warehouse_name, role_type, self.config.WAREHOUSE_ROLE_SUFFIX),
        )

    def build_integration_usage_grant(self, integration_name):
        return Grant(
            privilege="USAGE",
            on=ObjectType.INTEGRATION,
            name=Ident(integration_name),
        )

    def build_global_role_grant(self, global_role_name):
        return Grant(
            privilege="USAGE",
            on=ObjectType.ROLE,
            name=Ident(global_role_name),
        )

    def build_account_grant(self, privilege):
        return AccountGrant(privilege=privilege.upper())
