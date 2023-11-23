from snowddl.blueprint import NetworkPolicyBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class NetworkPolicyResolver(AbstractResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.NETWORK_POLICY

    def get_existing_objects(self):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW NETWORK POLICIES")

        for r in cur:
            # SHOW NETWORK POLICIES does not support LIKE filter, so it has to be applied manually in the code
            if self.config.env_prefix and not str(r["name"]).startswith(self.config.env_prefix):
                continue

            existing_objects[r["name"]] = {
                "name": r["name"],
                "entries_in_allowed_ip_list": r["entries_in_allowed_ip_list"],
                "entries_in_blocked_ip_list": r["entries_in_blocked_ip_list"],
                "comment": r["comment"] if r["comment"] else None,
            }

        for name, owner in self.engine.executor.map(self.get_owner_from_grant, existing_objects.keys()):
            if owner != self.engine.context.current_role:
                del existing_objects[name]

        return existing_objects

    def get_owner_from_grant(self, name):
        cur = self.engine.execute_meta(
            "SHOW GRANTS ON NETWORK POLICY {name:i}",
            {
                "name": name,
            },
        )

        for r in cur:
            # Assumption: OWNERSHIP grant always exist, exactly 1 row
            if r["privilege"] == "OWNERSHIP":
                return name, r["grantee_name"]

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(NetworkPolicyBlueprint)

    def create_object(self, bp: NetworkPolicyBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE NETWORK POLICY {name:i}",
            {
                "name": bp.full_name,
            },
        )

        query.append_nl(
            "ALLOWED_IP_LIST = ({allowed_ip_list})",
            {
                "allowed_ip_list": bp.allowed_ip_list,
            },
        )

        if bp.blocked_ip_list:
            query.append_nl(
                "BLOCKED_IP_LIST = ({blocked_ip_list})",
                {
                    "blocked_ip_list": bp.blocked_ip_list,
                },
            )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_network_policy)

        return ResolveResult.CREATE

    def compare_object(self, bp: NetworkPolicyBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        cur = self.engine.execute_meta(
            "DESC NETWORK POLICY {name:i}",
            {
                "name": bp.full_name,
            },
        )

        existing_allowed_ip_list = []
        existing_blocked_ip_list = []

        for r in cur:
            if r["name"] == "ALLOWED_IP_LIST":
                existing_allowed_ip_list = str(r["value"]).split(",")
            elif r["name"] == "BLOCKED_IP_LIST":
                existing_blocked_ip_list = str(r["value"]).split(",")

        if sorted(bp.allowed_ip_list) != sorted(existing_allowed_ip_list):
            self.engine.execute_unsafe_ddl(
                "ALTER NETWORK POLICY {name:i} SET ALLOWED_IP_LIST = ({allowed_ip_list})",
                {
                    "name": bp.full_name,
                    "allowed_ip_list": bp.allowed_ip_list,
                },
                condition=self.engine.settings.execute_network_policy,
            )

            result = ResolveResult.ALTER

        if sorted(bp.blocked_ip_list) != sorted(existing_blocked_ip_list):
            if bp.blocked_ip_list:
                self.engine.execute_unsafe_ddl(
                    "ALTER NETWORK POLICY {name:i} SET BLOCKED_IP_LIST = ({blocked_ip_list})",
                    {
                        "name": bp.full_name,
                        "blocked_ip_list": bp.blocked_ip_list,
                    },
                    condition=self.engine.settings.execute_network_policy,
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER NETWORK POLICY {name:i} SET BLOCKED_IP_LIST = ()",
                    {
                        "name": bp.full_name,
                    },
                    condition=self.engine.settings.execute_network_policy,
                )

            result = ResolveResult.ALTER

        if bp.comment != row["comment"]:
            self.engine.execute_unsafe_ddl(
                "ALTER NETWORK POLICY {name:i} SET COMMENT = {comment}",
                {
                    "name": bp.full_name,
                    "comment": bp.comment if bp.comment else None,
                },
                condition=self.engine.settings.execute_network_policy,
            )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP NETWORK POLICY {name:i}",
            {
                "name": row["name"],
            },
            condition=self.engine.settings.execute_network_policy,
        )

        return ResolveResult.DROP
