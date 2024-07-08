from snowddl.blueprint import OutboundShareBlueprint, Grant, build_grant_name_ident
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class OutboundShareResolver(AbstractResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.SHARE

    def get_existing_objects(self):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW SHARES")

        for r in cur:
            if r["kind"] != "OUTBOUND":
                continue

            if r["owner"] != self.engine.context.current_role:
                continue

            # Remove organization and account prefix, shares are referred in SQL by name only
            full_name = r["name"].split(".")[-1]

            existing_objects[full_name] = {
                "share": full_name,
                "database": r["database_name"],
                "accounts": r["to"].split(",") if r["to"] else [],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(OutboundShareBlueprint)

    def create_object(self, bp: OutboundShareBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE SHARE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_outbound_share)

        for bp_grant in bp.grants:
            self.create_grant(bp.full_name, bp_grant)

        if bp.accounts:
            self.set_accounts(bp)

        return ResolveResult.CREATE

    def compare_object(self, bp: OutboundShareBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        existing_grants = self.get_existing_share_grants(bp.full_name)

        for bp_grant in bp.grants:
            if bp_grant not in existing_grants:
                self.create_grant(bp.full_name, bp_grant)
                result = ResolveResult.GRANT

        for ex_grant in existing_grants:
            if ex_grant not in bp.grants:
                self.drop_grant(bp.full_name, ex_grant)
                result = ResolveResult.GRANT

        # SHOW SHARES command returns only 3 accounts for each OUTBOUND SHARE
        # If you have to set more accounts, it will work, but SnowDDL will be forced to run SET ACCOUNTS every time
        if bp.accounts and [str(a) for a in bp.accounts] != row["accounts"]:
            self.set_accounts(bp)
            result = ResolveResult.ALTER

        if bp.comment != row["comment"]:
            self.engine.execute_safe_ddl(
                "ALTER SHARE {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
                condition=self.engine.settings.execute_outbound_share,
            )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP SHARE {share_name:i}",
            {
                "share_name": row["share"],
            },
            condition=self.engine.settings.execute_outbound_share,
        )

        return ResolveResult.DROP

    def set_accounts(self, bp: OutboundShareBlueprint):
        query = self.engine.query_builder()

        query.append(
            "ALTER SHARE {full_name:i} SET ACCOUNTS = {accounts:i}",
            {
                "full_name": bp.full_name,
                "accounts": bp.accounts,
            },
        )

        if bp.share_restrictions is not None:
            query.append_nl("SHARE_RESTRICTIONS = {share_restrictions:b}", {"share_restrictions": bp.share_restrictions})

        self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_outbound_share)

    def create_grant(self, share_name, grant: Grant):
        self.engine.execute_unsafe_ddl(
            "GRANT {privilege:r} ON {on:r} {name:i} TO SHARE {share_name:i}",
            {
                "privilege": grant.privilege,
                "on": grant.on.singular,
                "name": grant.name,
                "share_name": share_name,
            },
            condition=self.engine.settings.execute_outbound_share,
        )

    def drop_grant(self, share_name, grant: Grant):
        self.engine.execute_unsafe_ddl(
            "REVOKE {privilege:r} ON {on:r} {name:i} FROM SHARE {share_name:i}",
            {
                "privilege": grant.privilege,
                "on": grant.on.singular,
                "name": grant.name,
                "share_name": share_name,
            },
            condition=self.engine.settings.execute_outbound_share,
        )

    def get_existing_share_grants(self, share_name):
        grants = []

        cur = self.engine.execute_meta(
            "SHOW GRANTS TO SHARE {share_name:i}",
            {
                "share_name": share_name,
            },
        )

        for r in cur:
            grants.append(
                Grant(
                    privilege=r["privilege"],
                    on=ObjectType[r["granted_on"]],
                    name=build_grant_name_ident(ObjectType[r["granted_on"]], r["name"]),
                )
            )

        return grants
