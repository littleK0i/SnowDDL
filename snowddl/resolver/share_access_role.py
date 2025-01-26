from snowddl.blueprint import (
    BusinessRoleBlueprint,
    DatabaseBlueprint,
    Grant,
    Ident,
    RoleBlueprint,
    SchemaBlueprint,
    build_role_ident,
)
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver, ObjectType


class ShareAccessRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.SHARE_ACCESS_ROLE_SUFFIX

    def get_blueprints(self):
        blueprints = []
        unique_share_names = set()

        for database_bp in self.config.get_blueprints_by_type(DatabaseBlueprint).values():
            for share_name in database_bp.owner_share_read:
                if isinstance(share_name, Ident):
                    unique_share_names.add(share_name)

        for schema_bp in self.config.get_blueprints_by_type(SchemaBlueprint).values():
            for share_name in schema_bp.owner_share_read:
                if isinstance(share_name, Ident):
                    unique_share_names.add(share_name)

        for business_role_bp in self.config.get_blueprints_by_type(BusinessRoleBlueprint).values():
            for share_name in business_role_bp.share_read:
                if isinstance(share_name, Ident):
                    unique_share_names.add(share_name)

        for share_name in unique_share_names:
            blueprints.append(self.get_blueprint_share_role(share_name))

        return {str(bp.full_name): bp for bp in blueprints}

    def get_blueprint_share_role(self, share_name: Ident):
        grants = [
            Grant(
                privilege="IMPORTED PRIVILEGES",
                on=ObjectType.DATABASE,
                name=share_name,
            ),
        ]

        return RoleBlueprint(
            full_name=build_role_ident(self.config.env_prefix, share_name, self.config.SHARE_ACCESS_ROLE_SUFFIX),
            grants=grants,
        )

    def get_existing_role_grants(self, role_name):
        # There is no way to detect specific grant of IMPORTED PRIVILEGES
        # SHOW GRANTS output is filled with whatever grants come with INBOUND SHARE
        # SHOW GRANTS with IMPORTED PRIVILEGES performance is awful, one call may take a few seconds
        # IMPORTED PRIVILEGES grant has to be emulated until we find a better option
        grants = [
            Grant(
                privilege="IMPORTED PRIVILEGES",
                on=ObjectType.DATABASE,
                name=Ident(role_name[len(self.config.env_prefix) : -len(self.get_role_suffix()) - 2]),
            )
        ]

        return role_name, grants, [], []
