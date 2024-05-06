from abc import abstractmethod

from snowddl.blueprint import (
    RoleBlueprint,
    Grant,
    AccountGrant,
    FutureGrant,
    SchemaIdent,
    SchemaObjectIdent,
    build_grant_name_ident_snowflake,
    build_future_grant_name_ident_snowflake,
)
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class AbstractRoleResolver(AbstractResolver):
    @abstractmethod
    def get_role_suffix(self) -> str:
        pass

    def get_object_type(self):
        return ObjectType.ROLE

    def get_existing_objects(self):
        existing_roles = {}

        cur = self.engine.execute_meta(
            "SHOW ROLES LIKE {pattern:lse}",
            {
                "pattern": (self.config.env_prefix, f"__{self.get_role_suffix()}"),
            },
        )

        for r in cur:
            if r["owner"] != self.engine.context.current_role:
                continue

            existing_roles[r["name"]] = {
                "role_name": r["name"],
                "comment": r["comment"] if r["comment"] else None,
            }

        # Process role grants in parallel
        for role_name, grants, account_grants, future_grants in self.engine.executor.map(
            self.get_existing_role_grants, existing_roles
        ):
            existing_roles[role_name]["grants"] = grants
            existing_roles[role_name]["account_grants"] = account_grants
            existing_roles[role_name]["future_grants"] = future_grants

        return existing_roles

    def get_existing_role_grants(self, role_name):
        grants = []
        account_grants = []
        future_grants = []

        # Normal and account grants
        cur = self.engine.execute_meta(
            "SHOW GRANTS TO ROLE {role_name:i}",
            {
                "role_name": role_name,
            },
        )

        for r in sorted(cur, key=self.sort_existing_grants):
            # Skip grants on unknown object types
            try:
                object_type = ObjectType[r["granted_on"]]
            except KeyError:
                continue

            # Snowflake bug: phantom MATERIALIZED VIEW when SEARCH OPTIMIZATION is enabled for table
            if object_type == ObjectType.MATERIALIZED_VIEW and str(r["name"]).endswith('IDX_MV_"'):
                continue

            if object_type == ObjectType.ACCOUNT:
                account_grants.append(AccountGrant(privilege=r["privilege"]))
            else:
                grants.append(
                    Grant(
                        privilege=r["privilege"],
                        on=object_type,
                        name=build_grant_name_ident_snowflake(r["name"], object_type),
                    )
                )

        # Future grants
        cur = self.engine.execute_meta(
            "SHOW FUTURE GRANTS TO ROLE {role_name:i}",
            {
                "role_name": role_name,
            },
        )

        for r in sorted(cur, key=self.sort_existing_grants):
            try:
                object_type = ObjectType[r["grant_on"]]
            except KeyError:
                # Skip future grants on unknown object types
                continue

            name = build_future_grant_name_ident_snowflake(r["name"])

            future_grants.append(
                FutureGrant(
                    privilege=r["privilege"],
                    on_future=object_type,
                    in_parent=ObjectType.SCHEMA if isinstance(name, SchemaIdent) else ObjectType.DATABASE,
                    name=name,
                )
            )

        return role_name, grants, account_grants, future_grants

    def sort_existing_grants(self, row):
        offset = 0

        # WRITE should be revoked before READ
        if row["privilege"] == "WRITE":
            offset = -1

        return (row.get("grant_on"), row.get("granted_on"), row["name"], offset, row["privilege"])

    def create_object(self, bp: RoleBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE ROLE {role_name:i}",
            {
                "role_name": bp.full_name,
            },
        )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        self.engine.execute_safe_ddl(query)

        self.engine.execute_safe_ddl(
            "GRANT ROLE {role_name:i} TO ROLE {current_role:i}",
            {
                "role_name": bp.full_name,
                "current_role": self.engine.context.current_role,
            },
        )

        for bp_grant in bp.grants:
            self.create_grant(bp.full_name, bp_grant)

        for bp_account_grant in bp.account_grants:
            self.create_account_grant(bp.full_name, bp_account_grant)

        for bp_future_grant in bp.future_grants:
            self.create_future_grant(bp.full_name, bp_future_grant)
            self.apply_future_grant_to_existing_objects(bp.full_name, bp_future_grant)

        return ResolveResult.CREATE

    def compare_object(self, bp: RoleBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if bp.comment != row["comment"]:
            self.engine.execute_safe_ddl(
                "ALTER ROLE {role_name:i} SET COMMENT = {comment}",
                {
                    "role_name": bp.full_name,
                    "comment": bp.comment,
                },
            )

            result = ResolveResult.ALTER

        # Normal grants
        for existing_grant in row["grants"]:
            if existing_grant not in bp.grants and self.grant_to_future_grant(existing_grant) not in bp.future_grants:
                self.drop_grant(bp.full_name, existing_grant)
                result = ResolveResult.GRANT

        for bp_grant in bp.grants:
            if bp_grant not in row["grants"]:
                self.create_grant(bp.full_name, bp_grant)
                result = ResolveResult.GRANT

        # Account grants
        for existing_account_grant in row["account_grants"]:
            if existing_account_grant not in bp.account_grants:
                self.drop_account_grant(bp.full_name, existing_account_grant)
                result = ResolveResult.GRANT

        for bp_account_grant in bp.account_grants:
            if bp_account_grant not in row["account_grants"]:
                self.create_account_grant(bp.full_name, bp_account_grant)
                result = ResolveResult.GRANT

        # Future grants
        for existing_future_grant in row["future_grants"]:
            if existing_future_grant not in bp.future_grants:
                self.drop_future_grant(bp.full_name, existing_future_grant)
                result = ResolveResult.GRANT

        for bp_future_grant in bp.future_grants:
            if bp_future_grant not in row["future_grants"]:
                self.create_future_grant(bp.full_name, bp_future_grant)
                self.apply_future_grant_to_existing_objects(bp.full_name, bp_future_grant)
                result = ResolveResult.GRANT
            elif self.engine.settings.refresh_future_grants:
                self.apply_future_grant_to_existing_objects(bp.full_name, bp_future_grant)
                result = ResolveResult.GRANT

        return result

    def drop_object(self, row: dict):
        # All other grants and future grants are destroyed automatically
        self.engine.execute_unsafe_ddl(
            "DROP ROLE {role_name:i}",
            {
                "role_name": row["role_name"],
            },
        )

        return ResolveResult.DROP

    def create_grant(self, role_name, grant: Grant):
        if grant.privilege == "USAGE" and grant.on == ObjectType.ROLE:
            self.engine.execute_safe_ddl(
                "GRANT ROLE {name:i} TO ROLE {role_name:i}",
                {
                    "name": grant.name,
                    "role_name": role_name,
                },
            )
        else:
            self.engine.execute_safe_ddl(
                "GRANT {privilege:r} ON {on:r} {name:i} TO ROLE {role_name:i}",
                {
                    "privilege": grant.privilege,
                    "on": grant.on.singular,
                    "name": grant.name,
                    "role_name": role_name,
                },
            )

    def drop_grant(self, role_name, grant: Grant):
        # OWNERSHIP can only be transferred, not revoked
        # We transfer ownership back to default "SnowDDL admin" role instead of REVOKE
        if grant.privilege == "OWNERSHIP":
            self.engine.execute_safe_ddl(
                "GRANT {privilege:r} ON {on:r} {name:i} TO ROLE {current_role:i} COPY CURRENT GRANTS",
                {
                    "privilege": grant.privilege,
                    "on": grant.on.singular,
                    "name": grant.name,
                    "current_role": self.engine.context.current_role,
                },
            )
        elif grant.privilege == "USAGE" and grant.on == ObjectType.ROLE:
            self.engine.execute_safe_ddl(
                "REVOKE ROLE {name:i} FROM ROLE {role_name:i}",
                {
                    "name": grant.name,
                    "role_name": role_name,
                },
            )
        else:
            self.engine.execute_safe_ddl(
                "REVOKE {privilege:r} ON {on:r} {name:i} FROM ROLE {role_name:i}",
                {
                    "privilege": grant.privilege,
                    "on": grant.on.singular,
                    "name": grant.name,
                    "role_name": role_name,
                },
            )

    def create_account_grant(self, role_name, account_grant: AccountGrant):
        self.engine.execute_safe_ddl(
            "GRANT {privilege:r} ON ACCOUNT TO ROLE {role_name:i}",
            {
                "privilege": account_grant.privilege,
                "role_name": role_name,
            },
        )

    def drop_account_grant(self, role_name, account_grant: AccountGrant):
        self.engine.execute_safe_ddl(
            "REVOKE {privilege:r} ON ACCOUNT FROM ROLE {role_name:i}",
            {
                "privilege": account_grant.privilege,
                "role_name": role_name,
            },
        )

    def create_future_grant(self, role_name, grant: FutureGrant):
        self.engine.execute_safe_ddl(
            "GRANT {privilege:r} ON FUTURE {on_future_plural:r} IN {in_parent_singular:r} {name:i} TO ROLE {role_name:i}",
            {
                "privilege": grant.privilege,
                "on_future_plural": grant.on_future.plural,
                "in_parent_singular": grant.in_parent.singular,
                "name": grant.name,
                "role_name": role_name,
            },
        )

    def drop_future_grant(self, role_name, grant: FutureGrant):
        self.engine.execute_safe_ddl(
            "REVOKE {privilege:r} ON FUTURE {on_future_plural:r} IN {in_parent_singular:r} {name:i} FROM ROLE {role_name:i}",
            {
                "privilege": grant.privilege,
                "on_future_plural": grant.on_future.plural,
                "in_parent_singular": grant.in_parent.singular,
                "name": grant.name,
                "role_name": role_name,
            },
        )

    def apply_future_grant_to_existing_objects(self, role_name, grant: FutureGrant):
        # Bulk grant on objects of type PIPE to ROLE is restricted (by Snowflake)
        if grant.on_future == ObjectType.PIPE:
            return

        self.engine.execute_safe_ddl(
            "GRANT {privilege:r} ON ALL {on_future_plural:r} IN {in_parent_singular:r} {name:i} TO ROLE {role_name:i}{copy_grants:r}",
            {
                "privilege": grant.privilege,
                "on_future_plural": grant.on_future.plural,
                "in_parent_singular": grant.in_parent.singular,
                "name": grant.name,
                "role_name": role_name,
                "copy_grants": " COPY CURRENT GRANTS" if (grant.privilege == "OWNERSHIP") else "",
            },
        )

    def grant_to_future_grant(self, grant: Grant):
        # Overloaded in Database and Schema role resolvers
        # Other role types are not expected to utilize furue grants
        return None
