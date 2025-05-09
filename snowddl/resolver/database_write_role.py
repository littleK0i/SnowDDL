from snowddl.blueprint import (
    DatabaseBlueprint,
    FutureGrant,
    Grant,
    RoleBlueprint,
    SchemaBlueprint,
    build_role_ident,
)
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver, ObjectType


class DatabaseWriteRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.DATABASE_ACCESS_ROLE_SUFFIX

    def get_role_type(self):
        return self.config.WRITE_ROLE_TYPE

    def get_blueprints(self):
        blueprints = []

        for database_bp in self.config.get_blueprints_by_type(DatabaseBlueprint).values():
            database_permission_model = self.config.get_permission_model(database_bp.permission_model)

            if database_permission_model.ruleset.create_database_write_role:
                blueprints.append(self.get_blueprint_write_role(database_bp))

        return {str(bp.full_name): bp for bp in blueprints}

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
