from snowddl.blueprint import (
    DatabaseIdent,
    SchemaRoleBlueprint,
    SchemaBlueprint,
    SchemaObjectIdent,
    Grant,
    FutureGrant,
    build_role_ident,
)
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver, ObjectType


class SchemaRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.SCHEMA_ROLE_SUFFIX

    def get_blueprints(self):
        blueprints = []

        for schema_bp in self.config.get_blueprints_by_type(SchemaBlueprint).values():
            schema_permission_model = self.config.get_permission_model(schema_bp.permission_model)

            if schema_permission_model.ruleset.create_schema_owner_role:
                blueprints.append(self.get_blueprint_owner_role(schema_bp))

            if schema_permission_model.ruleset.create_schema_write_role:
                blueprints.append(self.get_blueprint_write_role(schema_bp))

            if schema_permission_model.ruleset.create_schema_read_role:
                blueprints.append(self.get_blueprint_read_role(schema_bp))

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

        for model_create_grant in schema_permission_model.owner_create_grants:
            grants.append(
                Grant(
                    privilege=f"CREATE {model_create_grant.on.singular}",
                    on=ObjectType.SCHEMA,
                    name=schema_bp.full_name,
                )
            )

        for model_future_grant in schema_permission_model.owner_future_grants:
            future_grants.append(
                FutureGrant(
                    privilege=model_future_grant.privilege,
                    on_future=model_future_grant.on,
                    in_parent=ObjectType.SCHEMA,
                    name=schema_bp.full_name,
                )
            )

        depends_on = set()

        for additional_grant in schema_bp.owner_additional_grants:
            grants.append(additional_grant)

            # Dependency on another schema role
            if additional_grant.on == ObjectType.ROLE and str(additional_grant.name).endswith(self.get_role_suffix()):
                depends_on.add(additional_grant.name)

        for additional_account_grant in schema_bp.owner_additional_account_grants:
            account_grants.append(additional_account_grant)

        bp = SchemaRoleBlueprint(
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
            depends_on=depends_on,
        )

        return bp

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

        bp = SchemaRoleBlueprint(
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

    def get_blueprint_write_role(self, schema_bp: SchemaBlueprint):
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

        for model_future_grant in schema_permission_model.write_future_grants:
            future_grants.append(
                FutureGrant(
                    privilege=model_future_grant.privilege,
                    on_future=model_future_grant.on,
                    in_parent=ObjectType.SCHEMA,
                    name=schema_bp.full_name,
                )
            )

        bp = SchemaRoleBlueprint(
            full_name=build_role_ident(
                self.config.env_prefix,
                schema_bp.full_name.database,
                schema_bp.full_name.schema,
                self.config.WRITE_ROLE_TYPE,
                self.get_role_suffix(),
            ),
            grants=grants,
            future_grants=future_grants,
        )

        return bp

    def grant_to_future_grant(self, grant: Grant):
        if not grant.on.is_future_grant_supported:
            return None

        if isinstance(grant.name, SchemaObjectIdent):
            return FutureGrant(
                privilege=grant.privilege,
                on_future=grant.on,
                in_parent=ObjectType.SCHEMA,
                name=grant.name.schema_full_name,
            )

        return None
