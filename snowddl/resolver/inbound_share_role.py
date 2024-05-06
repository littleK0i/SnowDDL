from snowddl.blueprint import RoleBlueprint, DatabaseShareBlueprint, Grant, build_role_ident, build_grant_name_ident_snowflake
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver, ObjectType


class InboundShareRoleResolver(AbstractRoleResolver):
    skip_on_empty_blueprints = True

    def get_role_suffix(self):
        return self.config.INBOUND_SHARE_ROLE_SUFFIX

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
                        name=build_grant_name_ident_snowflake(r["name"], ObjectType.DATABASE),
                    )
                )

                break

        return role_name, grants, [], []

    def get_blueprints(self):
        blueprints = []

        for user in self.config.get_blueprints_by_type(DatabaseShareBlueprint).values():
            blueprints.append(self.get_blueprint_inbound_share_role(user))

        return {str(bp.full_name): bp for bp in blueprints}

    def get_blueprint_inbound_share_role(self, bp: DatabaseShareBlueprint):
        grants = []

        grants.append(
            Grant(
                privilege="IMPORTED PRIVILEGES",
                on=ObjectType.DATABASE,
                name=bp.full_name,
            )
        )

        return RoleBlueprint(
            full_name=build_role_ident(self.config.env_prefix, bp.full_name.database, self.get_role_suffix()),
            grants=grants,
            future_grants=[],
            comment=None,
        )
