from snowddl.blueprint import SchemaBlueprint, SchemaIdent, Grant, AccountGrant, ObjectType, Ident, build_role_ident
from snowddl.parser.abc_parser import AbstractParser
from snowddl.parser.database import database_json_schema


# fmt: off
schema_json_schema = {
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
        "owner_schema_read": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "owner_schema_write": {
            "type": "array",
            "items": {
                "type": "string"
            }
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


class SchemaParser(AbstractParser):
    def load_blueprints(self):
        for database_path in self.base_path.iterdir():
            if not database_path.is_dir():
                continue

            # Skip special sub-directories
            if database_path.name.startswith("__"):
                continue

            database_params = self.parse_single_file(database_path / "params.yaml", database_json_schema)

            for schema_path in database_path.iterdir():
                if not schema_path.is_dir():
                    continue

                schema_params = self.parse_single_file(schema_path / "params.yaml", schema_json_schema)

                combined_params = {
                    "is_transient": database_params.get("is_transient", False) or schema_params.get("is_transient", False),
                    "retention_time": schema_params.get("retention_time"),
                    "is_sandbox": database_params.get("is_sandbox", False) or schema_params.get("is_sandbox", False),
                }

                database_name = database_path.name.upper()
                schema_name = schema_path.name.upper()

                database_permission_model_name = database_params.get("permission_model", self.config.DEFAULT_PERMISSION_MODEL)
                schema_permission_model_name = schema_params.get("permission_model", database_permission_model_name)

                database_permission_model = self.config.get_permission_model(database_permission_model_name.upper())
                schema_permission_model = self.config.get_permission_model(schema_permission_model_name.upper())

                if database_permission_model.ruleset != schema_permission_model.ruleset:
                    raise ValueError(
                        f"Database [{database_name}] permission model ruleset does not match schema [{database_name}.{schema_name}] permission model ruleset"
                    )

                if not schema_permission_model.ruleset.create_schema_owner_role:
                    for k in schema_params:
                        if k.startswith("owner_"):
                            raise ValueError(
                                f"Cannot use parameter [{k}] for schema [{database_name}.{schema_name}], it should be configured on database level"
                            )

                owner_additional_grants = []
                owner_additional_account_grants = []

                for full_schema_name in schema_params.get("owner_schema_read", []):
                    owner_additional_grants.append(self.build_schema_role_grant(full_schema_name, self.config.READ_ROLE_TYPE))

                for full_schema_name in schema_params.get("owner_schema_write", []):
                    owner_additional_grants.append(self.build_schema_role_grant(full_schema_name, self.config.WRITE_ROLE_TYPE))

                for integration_name in schema_params.get("owner_integration_usage", []):
                    owner_additional_grants.append(self.build_integration_usage_grant(integration_name))

                for warehouse_name in schema_params.get("owner_warehouse_usage", []):
                    owner_additional_grants.append(self.build_warehouse_role_grant(warehouse_name, self.config.USAGE_ROLE_TYPE))

                for account_grant in schema_params.get("owner_account_grants", []):
                    owner_additional_account_grants.append(self.build_account_grant(account_grant))

                for global_role_name in schema_params.get("owner_global_roles", []):
                    owner_additional_grants.append(self.build_global_role_grant(global_role_name))

                bp = SchemaBlueprint(
                    full_name=SchemaIdent(self.env_prefix, database_name, schema_name),
                    permission_model=schema_permission_model,
                    is_transient=combined_params.get("is_transient", False),
                    retention_time=combined_params.get("retention_time", None),
                    is_sandbox=combined_params.get("is_sandbox", False),
                    owner_additional_grants=owner_additional_grants,
                    owner_additional_account_grants=owner_additional_account_grants,
                    comment=schema_params.get("comment", None),
                )

                self.config.add_blueprint(bp)

    def build_schema_role_grant(self, full_schema_name, role_type):
        database, schema = full_schema_name.split(".")

        return Grant(
            privilege="USAGE",
            on=ObjectType.ROLE,
            name=build_role_ident(self.env_prefix, database, schema, role_type, self.config.SCHEMA_ROLE_SUFFIX),
        )

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
