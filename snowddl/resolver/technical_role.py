from snowddl.blueprint import ObjectType, RoleBlueprint, SchemaBlueprint, TechnicalRoleBlueprint, Grant, FutureGrant
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver


class TechnicalRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.TECHNICAL_ROLE_SUFFIX

    def get_blueprints(self):
        return {
            full_name: self.transform_blueprint(business_role_bp)
            for full_name, business_role_bp in self.config.get_blueprints_by_type(TechnicalRoleBlueprint).items()
        }

    def transform_blueprint(self, technical_role_bp: TechnicalRoleBlueprint):
        grants = []
        future_grants = []

        for grant_pattern in technical_role_bp.grant_patterns:
            for obj_bp in self.config.get_blueprints_by_type_and_pattern(
                grant_pattern.on.blueprint_cls, grant_pattern.pattern
            ).values():
                grants.append(
                    Grant(
                        privilege=grant_pattern.privilege,
                        on=grant_pattern.on,
                        name=obj_bp.full_name,
                    ),
                )

        for future_grant_pattern in technical_role_bp.future_grant_patterns:
            for obj_bp in self.config.get_blueprints_by_type_and_pattern(
                future_grant_pattern.in_parent.blueprint_cls, future_grant_pattern.pattern
            ).values():
                future_grants.append(
                    FutureGrant(
                        privilege=future_grant_pattern.privilege,
                        on_future=future_grant_pattern.on_future,
                        in_parent=future_grant_pattern.in_parent,
                        name=obj_bp.full_name,
                    ),
                )

                if future_grant_pattern.in_parent != ObjectType.DATABASE:
                    continue

                # Future grants for each known schema on SCHEMA level
                # It is required to alleviate SCHEMA level grants overriding DATABASE level grants
                # https://docs.snowflake.com/en/sql-reference/sql/grant-privilege#future-grants-on-database-or-schema-objects
                for schema_bp in self.config.get_blueprints_by_type(SchemaBlueprint).values():
                    if obj_bp.full_name != schema_bp.full_name.database_full_name:
                        continue

                    future_grants.append(
                        FutureGrant(
                            privilege=future_grant_pattern.privilege,
                            on_future=future_grant_pattern.on_future,
                            in_parent=ObjectType.SCHEMA,
                            name=schema_bp.full_name,
                        )
                    )

        return RoleBlueprint(
            full_name=technical_role_bp.full_name,
            grants=grants,
            future_grants=future_grants,
            account_grants=technical_role_bp.account_grants,
            comment=technical_role_bp.comment,
        )
