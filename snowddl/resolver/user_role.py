from snowddl.blueprint import RoleBlueprint, UserBlueprint, Grant, build_role_ident
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver, ObjectType


class UserRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.USER_ROLE_SUFFIX

    def get_blueprints(self):
        blueprints = []

        for user in self.config.get_blueprints_by_type(UserBlueprint).values():
            blueprints.append(self.get_blueprint_user_role(user))

        return {str(bp.full_name): bp for bp in blueprints}

    def get_blueprint_user_role(self, user: UserBlueprint):
        grants = []

        for business_role in user.business_roles:
            grants.append(Grant(
                privilege="USAGE",
                on=ObjectType.ROLE,
                name=business_role,
            ))

        bp = RoleBlueprint(
            full_name=build_role_ident(self.config.env_prefix, user.full_name, self.get_role_suffix()),
            grants=grants,
            future_grants=[],
            comment=None,
        )

        return bp
