from snowddl.blueprint import (
    DatabaseBlueprint,
    FutureGrant,
    Grant,
    RoleBlueprint,
    SchemaBlueprint,
    SchemaIdent,
    SchemaObjectIdent,
    build_role_ident,
)
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver, ObjectType


class DatabaseAccessRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.DATABASE_ACCESS_ROLE_SUFFIX

    def get_blueprints(self):
        blueprints = []

        for database_bp in self.config.get_blueprints_by_type(DatabaseBlueprint).values():
            database_permission_model = self.config.get_permission_model(database_bp.permission_model)

            if database_permission_model.ruleset.create_database_owner_role:
                blueprints.append(self.get_blueprint_owner_role(database_bp))

            if database_permission_model.ruleset.create_database_write_role:
                blueprints.append(self.get_blueprint_write_role(database_bp))

            if database_permission_model.ruleset.create_database_read_role:
                blueprints.append(self.get_blueprint_read_role(database_bp))

        return {str(bp.full_name): bp for bp in blueprints}

    def get_blueprint_owner_role(self, database_bp: DatabaseBlueprint):
        grants = []
        account_grants = []
        future_grants = []
        depends_on = set()

        database_permission_model = self.config.get_permission_model(database_bp.permission_model)

        grants.append(
            Grant(
                privilege="USAGE",
                on=ObjectType.DATABASE,
                name=database_bp.full_name,
            )
        )

        grants.append(
            Grant(
                privilege="CREATE SCHEMA",
                on=ObjectType.DATABASE,
                name=database_bp.full_name,
            )
        )

        future_grants.append(
            FutureGrant(
                privilege="OWNERSHIP",
                on_future=ObjectType.SCHEMA,
                in_parent=ObjectType.DATABASE,
                name=database_bp.full_name,
            )
        )

        # Create grants
        for model_create_grant in database_permission_model.owner_create_grants:
            future_grants.append(
                FutureGrant(
                    privilege=f"CREATE {model_create_grant.on.singular}",
                    on_future=ObjectType.SCHEMA,
                    in_parent=ObjectType.DATABASE,
                    name=database_bp.full_name,
                )
            )

        # Owner-specific grants
        for database_name_pattern in database_bp.owner_database_write:
            grants.extend(self.build_database_role_grants(database_name_pattern, self.config.WRITE_ROLE_TYPE))

        for database_name_pattern in database_bp.owner_database_read:
            grants.extend(self.build_database_role_grants(database_name_pattern, self.config.READ_ROLE_TYPE))

        for integration_name in database_bp.owner_integration_usage:
            grants.append(self.build_integration_grant(integration_name))

        for share_name in database_bp.owner_share_read:
            grants.append(self.build_share_read_grant(share_name))

        for warehouse_name in database_bp.owner_warehouse_usage:
            grants.append(self.build_warehouse_role_grant(warehouse_name, self.config.USAGE_ROLE_TYPE))

        for account_grant in database_bp.owner_account_grants:
            account_grants.append(account_grant)

        for global_role_name in database_bp.owner_global_roles:
            grants.append(self.build_global_role_grant(global_role_name))

        # Future grants on DATABASE level
        for model_future_grant in database_permission_model.owner_future_grants:
            future_grants.append(
                FutureGrant(
                    privilege=model_future_grant.privilege,
                    on_future=model_future_grant.on,
                    in_parent=ObjectType.DATABASE,
                    name=database_bp.full_name,
                )
            )

        # Future grants for each known schema on SCHEMA level
        # It is required to alleviate SCHEMA level grants overriding DATABASE level grants
        # https://docs.snowflake.com/en/sql-reference/sql/grant-privilege#future-grants-on-database-or-schema-objects
        for schema_bp in self.config.get_blueprints_by_type(SchemaBlueprint).values():
            if database_bp.full_name != schema_bp.full_name.database_full_name:
                continue

            for model_future_grant in database_permission_model.owner_future_grants:
                future_grants.append(
                    FutureGrant(
                        privilege=model_future_grant.privilege,
                        on_future=model_future_grant.on,
                        in_parent=ObjectType.SCHEMA,
                        name=schema_bp.full_name,
                    )
                )

        # Add explicit dependencies on other database roles
        for g in grants:
            if g.on == ObjectType.ROLE and str(g.name).endswith(self.get_role_suffix()):
                depends_on.add(g.name)

        bp = RoleBlueprint(
            full_name=build_role_ident(
                self.config.env_prefix, database_bp.full_name.database, self.config.OWNER_ROLE_TYPE, self.get_role_suffix()
            ),
            grants=grants,
            account_grants=account_grants,
            future_grants=future_grants,
            depends_on=depends_on,
        )

        return bp

    def get_blueprint_read_role(self, database_bp: DatabaseBlueprint):
        grants = []
        future_grants = []

        database_permission_model = self.config.get_permission_model(database_bp.permission_model)

        grants.append(
            Grant(
                privilege="USAGE",
                on=ObjectType.DATABASE,
                name=database_bp.full_name,
            )
        )

        future_grants.append(
            FutureGrant(
                privilege="USAGE",
                on_future=ObjectType.SCHEMA,
                in_parent=ObjectType.DATABASE,
                name=database_bp.full_name,
            )
        )

        # Future grants on DATABASE level
        for model_future_grant in database_permission_model.read_future_grants:
            future_grants.append(
                FutureGrant(
                    privilege=model_future_grant.privilege,
                    on_future=model_future_grant.on,
                    in_parent=ObjectType.DATABASE,
                    name=database_bp.full_name,
                )
            )

        # Future grants for each known schema on SCHEMA level
        # It is required to alleviate SCHEMA level grants overriding DATABASE level
        # https://docs.snowflake.com/en/sql-reference/sql/grant-privilege#future-grants-on-database-or-schema-objects
        for schema_bp in self.config.get_blueprints_by_type(SchemaBlueprint).values():
            if database_bp.full_name != schema_bp.full_name.database_full_name:
                continue

            for model_future_grant in database_permission_model.read_future_grants:
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
                self.config.env_prefix, database_bp.full_name.database, self.config.READ_ROLE_TYPE, self.get_role_suffix()
            ),
            grants=grants,
            future_grants=future_grants,
        )

        return bp

    def get_blueprint_write_role(self, database_bp: DatabaseBlueprint):
        grants = []
        future_grants = []

        database_permission_model = self.config.get_permission_model(database_bp.permission_model)

        grants.append(
            Grant(
                privilege="USAGE",
                on=ObjectType.DATABASE,
                name=database_bp.full_name,
            )
        )

        future_grants.append(
            FutureGrant(
                privilege="USAGE",
                on_future=ObjectType.SCHEMA,
                in_parent=ObjectType.DATABASE,
                name=database_bp.full_name,
            )
        )

        # Future grants on DATABASE level
        for model_future_grant in database_permission_model.write_future_grants:
            future_grants.append(
                FutureGrant(
                    privilege=model_future_grant.privilege,
                    on_future=model_future_grant.on,
                    in_parent=ObjectType.DATABASE,
                    name=database_bp.full_name,
                )
            )

        # Future grants for each known schema on SCHEMA level
        # It is required to alleviate SCHEMA level grants overriding DATABASE level
        # https://docs.snowflake.com/en/sql-reference/sql/grant-privilege#future-grants-on-database-or-schema-objects
        for schema_bp in self.config.get_blueprints_by_type(SchemaBlueprint).values():
            if database_bp.full_name != schema_bp.full_name.database_full_name:
                continue

            for model_future_grant in database_permission_model.write_future_grants:
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
                self.config.env_prefix, database_bp.full_name.database, self.config.WRITE_ROLE_TYPE, self.get_role_suffix()
            ),
            grants=grants,
            future_grants=future_grants,
        )

        return bp

    def grant_to_future_grant(self, grant: Grant):
        if not grant.on.is_future_grant_supported:
            return None

        if isinstance(grant.name, (SchemaIdent, SchemaObjectIdent)):
            return FutureGrant(
                privilege=grant.privilege,
                on_future=grant.on,
                in_parent=ObjectType.DATABASE,
                name=grant.name.database_full_name,
            )

        return None
