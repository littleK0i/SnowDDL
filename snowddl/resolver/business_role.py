from snowddl.blueprint import BusinessRoleBlueprint
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver


class BusinessRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.BUSINESS_ROLE_SUFFIX

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(BusinessRoleBlueprint)
