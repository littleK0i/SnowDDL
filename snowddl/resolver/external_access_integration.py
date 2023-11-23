from snowddl.blueprint import ExternalAccessIntegrationBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class ExternalAccessIntegrationResolver(AbstractResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.EXTERNAL_ACCESS_INTEGRATION

    def get_existing_objects(self):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW EXTERNAL ACCESS INTEGRATIONS LIKE {env_prefix:ls}",
            {
                "env_prefix": self.config.env_prefix,
            },
        )

        for r in cur:
            existing_objects[r["name"]] = {
                "name": r["name"],
                "enabled": r["enabled"],
                "comment": r["comment"] if r["comment"] else None,
            }

        for name, owner in self.engine.executor.map(self.get_owner_from_grant, existing_objects.keys()):
            if owner != self.engine.context.current_role:
                del existing_objects[name]

        return existing_objects

    def get_owner_from_grant(self, name):
        cur = self.engine.execute_meta(
            "SHOW GRANTS ON INTEGRATION {name:i}",
            {
                "name": name,
            },
        )

        for r in cur:
            # Assumption: OWNERSHIP grant always exist, exactly 1 row
            if r["privilege"] == "OWNERSHIP":
                return name, r["grantee_name"]

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(ExternalAccessIntegrationBlueprint)

    def create_object(self, bp: ExternalAccessIntegrationBlueprint):
        common_query = self._build_common_external_access_integration_sql(bp)
        create_query = self.engine.query_builder()

        create_query.append(
            "CREATE EXTERNAL ACCESS INTEGRATION {name:i}",
            {
                "name": bp.full_name,
            },
        )

        create_query.append_nl(common_query)
        self.engine.execute_safe_ddl(create_query)

        self.engine.execute_safe_ddl(
            "COMMENT ON INTEGRATION {name:i} IS {comment}",
            {
                "name": bp.full_name,
                "comment": common_query.add_short_hash(bp.comment),
            },
        )

        return ResolveResult.CREATE

    def compare_object(self, bp: ExternalAccessIntegrationBlueprint, row: dict):
        common_query = self._build_common_external_access_integration_sql(bp)

        if not common_query.compare_short_hash(row["comment"]):
            replace_query = self.engine.query_builder()

            replace_query.append(
                "CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION {name:i}",
                {
                    "name": bp.full_name,
                },
            )

            replace_query.append_nl(common_query)
            self.engine.execute_safe_ddl(replace_query)

            self.engine.execute_safe_ddl(
                "COMMENT ON INTEGRATION {name:i} IS {comment}",
                {
                    "name": bp.full_name,
                    "comment": common_query.add_short_hash(bp.comment),
                },
            )

            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP EXTERNAL ACCESS INTEGRATION {name:i}",
            {
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_common_external_access_integration_sql(self, bp: ExternalAccessIntegrationBlueprint):
        query = self.engine.query_builder()

        query.append_nl(
            "ALLOWED_NETWORK_RULES = ({allowed_network_rules:i})",
            {
                "allowed_network_rules": bp.allowed_network_rules,
            },
        )

        if bp.allowed_api_authentication_integrations:
            query.append_nl(
                "ALLOWED_API_AUTHENTICATION_INTEGRATIONS = ({allowed_api_authentication_integrations:i})",
                {
                    "allowed_api_authentication_integrations": bp.allowed_api_authentication_integrations,
                },
            )

        if bp.allowed_authentication_secrets:
            query.append_nl(
                "ALLOWED_AUTHENTICATION_SECRETS = ({allowed_authentication_secrets:i})",
                {
                    "allowed_authentication_secrets": bp.allowed_authentication_secrets,
                },
            )

        query.append_nl(
            "ENABLED = {enabled:b}",
            {
                "enabled": bp.enabled,
            },
        )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        return query
