from snowddl.blueprint import (
    DatabaseIdent,
    FutureGrant,
    Grant,
    RoleBlueprint,
    SchemaBlueprint,
    build_role_ident,
)
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver, ObjectType


class SchemaReadRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.SCHEMA_ACCESS_ROLE_SUFFIX

    def get_role_type(self):
        return self.config.READ_ROLE_TYPE

    def get_blueprints(self):
        blueprints = []

        for schema_bp in self.config.get_blueprints_by_type(SchemaBlueprint).values():
            schema_permission_model = self.config.get_permission_model(schema_bp.permission_model)

            if schema_permission_model.ruleset.create_schema_read_role:
                blueprints.append(self.get_blueprint_read_role(schema_bp))

        return {str(bp.full_name): bp for bp in blueprints}

    def get_blueprint_read_role(self, schema_bp: SchemaBlueprint):
        grants = []
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

        for model_future_grant in schema_permission_model.read_future_grants:
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
                self.config.READ_ROLE_TYPE,
                self.get_role_suffix(),
            ),
            grants=grants,
            future_grants=future_grants,
        )

        return bp
