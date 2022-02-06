from snowddl.blueprint import TechRoleBlueprint
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver


class TechRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.TECH_ROLE_SUFFIX

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(TechRoleBlueprint)
