from snowddl.blueprint import (
    DatabaseIdent,
    FutureGrant,
    Grant,
    RoleBlueprint,
    SchemaBlueprint,
    build_role_ident,
)
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver, ObjectType


class SchemaOwnerRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.SCHEMA_ACCESS_ROLE_SUFFIX

    def get_role_type(self):
        return self.config.OWNER_ROLE_TYPE

    def get_blueprints(self):
        blueprints = []

        for schema_bp in self.config.get_blueprints_by_type(SchemaBlueprint).values():
            schema_permission_model = self.config.get_permission_model(schema_bp.permission_model)

            if schema_permission_model.ruleset.create_schema_owner_role:
                blueprints.append(self.get_blueprint_owner_role(schema_bp))

        return {str(bp.full_name): bp for bp in blueprints}

    def get_blueprint_owner_role(self, schema_bp: SchemaBlueprint):
        grants = []
        account_grants = []
        future_grants = []

        schema_permission_model = self.config.get_permission_model(schema_bp.permission_model)

        grants.append(
            Grant(
                privilege="USAGE",
                on=ObjectType.DATABASE,
                name=DatabaseIdent(schema_bp.full_name.env_prefix, schema_bp.full_name.database),
            )
        )

        grants.append(
            Grant(
                privilege="USAGE",
                on=ObjectType.SCHEMA,
                name=schema_bp.full_name,
            )
        )

        # Iceberg-related grants
        if schema_bp.external_volume:
            grants.append(
                Grant(
                    privilege="USAGE",
                    on=ObjectType.VOLUME,
                    name=schema_bp.external_volume,
                )
            )

        if schema_bp.catalog:
            grants.append(
                Grant(
                    privilege="USAGE",
                    on=ObjectType.INTEGRATION,
                    name=schema_bp.catalog,
                )
            )

        # Create grants
        for model_create_grant in schema_permission_model.owner_create_grants:
            grants.append(
                Grant(
                    privilege=f"CREATE {model_create_grant.on.singular}",
                    on=ObjectType.SCHEMA,
                    name=schema_bp.full_name,
                )
            )

        # Owner-specific grants
        for database_name_pattern in schema_bp.owner_database_write:
            grants.extend(self.build_database_role_grants(database_name_pattern, self.config.WRITE_ROLE_TYPE))

        for database_name_pattern in schema_bp.owner_database_read:
            grants.extend(self.build_database_role_grants(database_name_pattern, self.config.READ_ROLE_TYPE))

        for schema_name_pattern in schema_bp.owner_schema_write:
            grants.extend(self.build_schema_role_grants(schema_name_pattern, self.config.WRITE_ROLE_TYPE))

        for schema_name_pattern in schema_bp.owner_schema_read:
            grants.extend(self.build_schema_role_grants(schema_name_pattern, self.config.READ_ROLE_TYPE))

        for integration_name in schema_bp.owner_integration_usage:
            grants.append(self.build_integration_grant(integration_name))

        for share_name in schema_bp.owner_share_read:
            grants.append(self.build_share_read_grant(share_name))

        for warehouse_name in schema_bp.owner_warehouse_usage:
            grants.append(self.build_warehouse_role_grant(warehouse_name, self.config.USAGE_ROLE_TYPE))

        for account_grant in schema_bp.owner_account_grants:
            account_grants.append(account_grant)

        for global_role_name in schema_bp.owner_global_roles:
            grants.append(self.build_global_role_grant(global_role_name))

        # Future grants on SCHEMA level
        for model_future_grant in schema_permission_model.owner_future_grants:
            future_grants.append(
                FutureGrant(
                    privilege=model_future_grant.privilege,
                    on_future=model_future_grant.on,
                    in_parent=ObjectType.SCHEMA,
                    name=schema_bp.full_name,
                )
            )

        bp = RoleBlueprint(
            full_name=build_role_ident(
                self.config.env_prefix,
                schema_bp.full_name.database,
                schema_bp.full_name.schema,
                self.config.OWNER_ROLE_TYPE,
                self.get_role_suffix(),
            ),
            grants=grants,
            account_grants=account_grants,
            future_grants=future_grants,
        )

        return bp
