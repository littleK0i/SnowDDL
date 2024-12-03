from snowddl.blueprint import RoleBlueprint, TechnicalRoleBlueprint, Grant
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

        return RoleBlueprint(
            full_name=technical_role_bp.full_name,
            grants=grants,
            account_grants=technical_role_bp.account_grants,
            comment=technical_role_bp.comment,
        )
