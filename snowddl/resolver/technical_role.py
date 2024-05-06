from snowddl.blueprint import TechnicalRoleBlueprint
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver


class TechnicalRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.TECHNICAL_ROLE_SUFFIX

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(TechnicalRoleBlueprint)
