from snowddl.blueprint import AccountObjectIdent, NetworkPolicyBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType

from json import loads


class NetworkPolicyResolver(AbstractResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.NETWORK_POLICY

    def get_existing_objects(self):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW NETWORK POLICIES LIKE {env_prefix:ls}",
            {
                "env_prefix": self.config.env_prefix,
            },
        )

        for r in cur:
            existing_objects[r["name"]] = {
                "name": r["name"],
                "comment": r["comment"] if r["comment"] else None,
            }

        # Ownership is not available in SHOW NETWORK POLICIES
        # But it can be derived from grants
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
        self._create_policy(bp)
        self._apply_policy_refs(bp, skip_existing=True)

        return ResolveResult.CREATE

    def compare_object(self, bp: NetworkPolicyBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        cur = self.engine.execute_meta(
            "DESC NETWORK POLICY {name:i}",
            {
                "name": bp.full_name,
            },
        )

        existing_allowed_network_rule_list = []
        existing_blocked_network_rule_list = []
        existing_allowed_ip_list = []
        existing_blocked_ip_list = []

        for r in cur:
            if r["name"] == "ALLOWED_NETWORK_RULE_LIST":
                existing_allowed_network_rule_list = [v["fullyQualifiedRuleName"] for v in loads(r["value"])]
            elif r["name"] == "BLOCKED_NETWORK_RULE_LIST":
                existing_blocked_network_rule_list = [v["fullyQualifiedRuleName"] for v in loads(r["value"])]
            elif r["name"] == "ALLOWED_IP_LIST":
                existing_allowed_ip_list = str(r["value"]).split(",")
            elif r["name"] == "BLOCKED_IP_LIST":
                existing_blocked_ip_list = str(r["value"]).split(",")

        if sorted(map(str, bp.allowed_network_rule_list)) != sorted(existing_allowed_network_rule_list):
            if bp.allowed_network_rule_list:
                self.engine.execute_unsafe_ddl(
                    "ALTER NETWORK POLICY {name:i} SET ALLOWED_NETWORK_RULE_LIST = ({allowed_network_rule_list:i})",
                    {
                        "name": bp.full_name,
                        "allowed_network_rule_list": bp.allowed_network_rule_list,
                    },
                    condition=self.engine.settings.execute_network_policy,
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER NETWORK POLICY {name:i} UNSET ALLOWED_NETWORK_RULE_LIST",
                    {
                        "name": bp.full_name,
                    },
                    condition=self.engine.settings.execute_network_policy,
                )

            result = ResolveResult.ALTER

        if sorted(map(str, bp.blocked_network_rule_list)) != sorted(existing_blocked_network_rule_list):
            if bp.blocked_network_rule_list:
                self.engine.execute_unsafe_ddl(
                    "ALTER NETWORK POLICY {name:i} SET BLOCKED_NETWORK_RULE_LIST = ({blocked_network_rule_list:i})",
                    {
                        "name": bp.full_name,
                        "blocked_network_rule_list": bp.blocked_network_rule_list,
                    },
                    condition=self.engine.settings.execute_network_policy,
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER NETWORK POLICY {name:i} UNSET BLOCKED_NETWORK_RULE_LIST",
                    {
                        "name": bp.full_name,
                    },
                    condition=self.engine.settings.execute_network_policy,
                )

            result = ResolveResult.ALTER

        if sorted(bp.allowed_ip_list) != sorted(existing_allowed_ip_list):
            if bp.allowed_ip_list:
                self.engine.execute_unsafe_ddl(
                    "ALTER NETWORK POLICY {name:i} SET ALLOWED_IP_LIST = ({blocked_ip_list})",
                    {
                        "name": bp.full_name,
                        "blocked_ip_list": bp.allowed_ip_list,
                    },
                    condition=self.engine.settings.execute_network_policy,
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER NETWORK POLICY {name:i} UNSET ALLOWED_IP_LIST",
                    {
                        "name": bp.full_name,
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
                    "ALTER NETWORK POLICY {name:i} UNSET BLOCKED_IP_LIST",
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

        if self._apply_policy_refs(bp):
            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        policy_name = AccountObjectIdent("", row["name"])

        self._drop_policy_refs(policy_name)
        self._drop_policy(policy_name)

        return ResolveResult.DROP

    def _create_policy(self, bp: NetworkPolicyBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE NETWORK POLICY {name:i}",
            {
                "name": bp.full_name,
            },
        )

        if bp.allowed_network_rule_list:
            query.append_nl(
                "ALLOWED_NETWORK_RULE_LIST = ({allowed_network_rule_list:i})",
                {
                    "allowed_network_rule_list": bp.allowed_network_rule_list,
                },
            )

        if bp.blocked_network_rule_list:
            query.append_nl(
                "BLOCKED_NETWORK_RULE_LIST = ({blocked_network_rule_list:i})",
                {
                    "blocked_network_rule_list": bp.blocked_network_rule_list,
                },
            )

        if bp.allowed_ip_list:
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

    def _drop_policy(self, policy_name: AccountObjectIdent):
        self.engine.execute_unsafe_ddl(
            "DROP NETWORK POLICY {full_name:i}",
            {"full_name": policy_name},
            condition=self.engine.settings.execute_network_policy,
        )

    def _apply_policy_refs(self, bp: NetworkPolicyBlueprint, skip_existing=False):
        existing_policy_refs = {} if skip_existing else self._get_existing_policy_refs(bp.full_name)
        applied_change = False

        for ref in bp.references:
            if ref.object_type == ObjectType.ACCOUNT:
                ref_key = ref.object_type.name
            else:
                ref_key = f"{ref.object_type.name}|{ref.object_name}"

            # Policy was applied before
            if ref_key in existing_policy_refs:
                del existing_policy_refs[ref_key]
                continue

            if ref.object_type == ObjectType.ACCOUNT:
                # Apply new policy for ACCOUNT
                self.engine.execute_unsafe_ddl(
                    "ALTER ACCOUNT SET NETWORK_POLICY = {policy_name:i}",
                    {
                        "policy_name": bp.full_name,
                    },
                    condition=self.engine.settings.execute_network_policy and self.engine.settings.execute_account_level_policy,
                )
            else:
                # Apply new policy for USER (and other object types in future?)
                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {object_name:i} SET NETWORK_POLICY = {policy_name:i}",
                    {
                        "object_type": ref.object_type.name,
                        "object_name": ref.object_name,
                        "policy_name": bp.full_name,
                    },
                    condition=self.engine.settings.execute_network_policy,
                )

            applied_change = True

        # Remove remaining policy references which no longer exist in blueprint
        for existing_ref in existing_policy_refs.values():
            if existing_ref["object_type"] == ObjectType.ACCOUNT.name:
                self.engine.execute_unsafe_ddl(
                    "ALTER ACCOUNT UNSET NETWORK_POLICY",
                    condition=self.engine.settings.execute_network_policy and self.engine.settings.execute_account_level_policy,
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {object_name:i} UNSET NETWORK_POLICY",
                    {
                        "object_type": existing_ref["object_type"],
                        "object_name": existing_ref["name"],
                    },
                    condition=self.engine.settings.execute_network_policy,
                )

            applied_change = True

        return applied_change

    def _drop_policy_refs(self, policy_name: AccountObjectIdent):
        existing_policy_refs = self._get_existing_policy_refs(policy_name)

        for existing_ref in existing_policy_refs.values():
            if existing_ref["object_type"] == ObjectType.ACCOUNT.name:
                self.engine.execute_unsafe_ddl(
                    "ALTER ACCOUNT UNSET NETWORK_POLICY",
                    condition=self.engine.settings.execute_network_policy and self.engine.settings.execute_account_level_policy,
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {object_name:i} UNSET NETWORK_POLICY",
                    {
                        "object_type": existing_ref["object_type"],
                        "object_name": existing_ref["name"],
                    },
                    condition=self.engine.settings.execute_network_policy,
                )

    def _get_existing_policy_refs(self, policy_name: AccountObjectIdent):
        existing_policy_refs = {}

        cur = self.engine.execute_meta(
            "SELECT * FROM TABLE(snowflake.information_schema.policy_references(policy_name => {policy_name}, policy_kind => {policy_kind}))",
            {
                "policy_name": policy_name,
                "policy_kind": self.object_type.name,
            },
        )

        for r in cur:
            if r["REF_ENTITY_DOMAIN"] == ObjectType.ACCOUNT.name:
                ref_key = r["REF_ENTITY_DOMAIN"]
            else:
                ref_key = f"{r['REF_ENTITY_DOMAIN']}|{r['REF_ENTITY_NAME']}"

            existing_policy_refs[ref_key] = {
                "object_type": r["REF_ENTITY_DOMAIN"],
                "name": r["REF_ENTITY_NAME"],
            }

        return existing_policy_refs
