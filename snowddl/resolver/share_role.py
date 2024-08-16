from snowddl.blueprint import ShareRoleBlueprint, Grant, build_grant_name_ident
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver, ObjectType


class ShareRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.SHARE_ROLE_SUFFIX

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(ShareRoleBlueprint)

    def get_existing_role_grants(self, role_name):
        # There is no way to detect grant of IMPORTED PRIVILEGES directly
        # SHOW GRANTS output is filled with whatever grants come with INBOUND SHARE
        # IMPORTED PRIVILEGES grant has to be emulated
        grants = []

        cur = self.engine.execute_meta(
            "SHOW GRANTS TO ROLE {role_name:i}",
            {
                "role_name": role_name,
            },
        )

        for r in cur:
            # Convert DATABASE.USAGE grant into IMPORTED PRIVILEGES
            # Ignore everything else
            if r["privilege"] == "USAGE" and r["granted_on"] == "DATABASE":
                grants.append(
                    Grant(
                        privilege="IMPORTED PRIVILEGES",
                        on=ObjectType.DATABASE,
                        name=build_grant_name_ident(ObjectType.DATABASE, r["name"]),
                    )
                )

                break

        return role_name, grants, [], []
