from snowddl.blueprint import AuthenticationPolicyBlueprint, ObjectType, SchemaObjectIdent
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult


class AuthenticationPolicyResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.AUTHENTICATION_POLICY

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW AUTHENTICATION POLICIES IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            full_name = f"{r['database_name']}.{r['schema_name']}.{r['name']}"

            existing_objects[full_name] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(AuthenticationPolicyBlueprint)

    def create_object(self, bp: AuthenticationPolicyBlueprint):
        self._create_policy(bp)
        self._apply_policy_refs(bp, skip_existing=True)

        return ResolveResult.CREATE

    def compare_object(self, bp: AuthenticationPolicyBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if self._compare_policy(bp, row):
            result = ResolveResult.ALTER

        if self._apply_policy_refs(bp):
            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self._drop_policy_refs(SchemaObjectIdent("", row["database"], row["schema"], row["name"]))
        self._drop_policy(SchemaObjectIdent("", row["database"], row["schema"], row["name"]))

        return ResolveResult.DROP

    def _create_policy(self, bp: AuthenticationPolicyBlueprint):
        common_query = self._build_common_authentication_policy_sql(bp)
        create_query = self.engine.query_builder()

        create_query.append(
            "CREATE AUTHENTICATION POLICY {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        create_query.append(common_query)
        self.engine.execute_unsafe_ddl(create_query, condition=self.engine.settings.execute_authentication_policy)

        self.engine.execute_unsafe_ddl(
            "COMMENT ON AUTHENTICATION POLICY {full_name:i} IS {comment}",
            {
                "full_name": bp.full_name,
                "comment": common_query.add_short_hash(bp.comment),
            },
            condition=self.engine.settings.execute_authentication_policy
        )

    def _compare_policy(self, bp: AuthenticationPolicyBlueprint, row: dict):
        common_query = self._build_common_authentication_policy_sql(bp)

        if not common_query.compare_short_hash(row["comment"]):
            alter_query = self.engine.query_builder()

            alter_query.append(
                "CREATE OR ALTER AUTHENTICATION POLICY {full_name:i}",
                {
                    "full_name": bp.full_name,
                },
            )

            alter_query.append(common_query)
            self.engine.execute_unsafe_ddl(alter_query, condition=self.engine.settings.execute_authentication_policy)

            self.engine.execute_safe_ddl(
                "COMMENT ON AUTHENTICATION POLICY {full_name:i} IS {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": common_query.add_short_hash(bp.comment),
                },
                condition=self.engine.settings.execute_authentication_policy
            )

            return True

        return False

    def _build_common_authentication_policy_sql(self, bp: AuthenticationPolicyBlueprint):
        query = self.engine.query_builder()

        if bp.authentication_methods:
            query.append_nl(
                "AUTHENTICATION_METHODS = ({authentication_methods})",
                {
                    "authentication_methods": bp.authentication_methods,
                },
            )

        if bp.mfa_authentication_methods:
            query.append_nl(
                "MFA_AUTHENTICATION_METHODS = ({mfa_authentication_methods})",
                {
                    "mfa_authentication_methods": bp.mfa_authentication_methods,
                },
            )

        if bp.mfa_enrollment:
            query.append_nl(
                "MFA_ENROLLMENT = {mfa_enrollment}",
                {
                    "mfa_enrollment": bp.mfa_enrollment,
                },
            )

        if bp.mfa_policy:
            query.append_nl("MFA_POLICY = (")

            for param_name, param_value in bp.mfa_policy.items():
                query.append(
                    "{param_name:r} = {param_value:dp}",
                    {
                        "param_name": param_name,
                        "param_value": param_value,
                    }
                )

            query.append(")")

        if bp.client_types:
            query.append_nl(
                "CLIENT_TYPES = ({client_types})",
                {
                    "client_types": bp.client_types,
                },
            )

        if bp.client_policy:
            query.append_nl("CLIENT_POLICY = (")

            for client_name, client_params in bp.client_policy.items():
                query.append(
                    "{client_name:r} = (",
                    {
                        "client_name": client_name,
                    }
                )

                for param_name, param_value in client_params.items():
                    query.append(
                        "{param_name:r} = {param_value:dp}",
                        {
                            "param_name": param_name,
                            "param_value": param_value,
                        }
                    )

                query.append(")")

            query.append(")")

        if bp.security_integrations:
            query.append_nl(
                "SECURITY_INTEGRATIONS = ({security_integrations})",
                {
                    "security_integrations": bp.security_integrations,
                },
            )

        if bp.pat_policy:
            query.append_nl("PAT_POLICY = (")

            for param_name, param_value in bp.pat_policy.items():
                query.append(
                    "{param_name:r} = {param_value:dp}",
                    {
                        "param_name": param_name,
                        "param_value": param_value,
                    }
                )

            query.append(")")

        if bp.workload_identity_policy:
            query.append_nl("WORKLOAD_IDENTITY_POLICY = (")

            for param_name, param_value in bp.workload_identity_policy.items():
                query.append(
                    "{param_name:r} = {param_value:dp}",
                    {
                        "param_name": param_name,
                        "param_value": param_value,
                    }
                )

            query.append(")")

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        return query

    def _drop_policy(self, policy: SchemaObjectIdent):
        self.engine.execute_unsafe_ddl(
            "DROP AUTHENTICATION POLICY {full_name:i}",
            {"full_name": policy},
            condition=self.engine.settings.execute_authentication_policy,
        )

    def _apply_policy_refs(self, bp: AuthenticationPolicyBlueprint, skip_existing=False):
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
                self.engine.execute_unsafe_ddl(
                    "ALTER ACCOUNT SET AUTHENTICATION POLICY {policy_name:i} FORCE",
                    {
                        "policy_name": bp.full_name,
                    },
                    condition=self.engine.settings.execute_authentication_policy
                    and self.engine.settings.execute_account_level_policy,
                )
            else:
                # Apply new policy for USER (and other object types in future?)
                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {object_name:i} SET AUTHENTICATION POLICY {policy_name:i} FORCE",
                    {
                        "object_type": ref.object_type.name,
                        "object_name": ref.object_name,
                        "policy_name": bp.full_name,
                    },
                    condition=self.engine.settings.execute_authentication_policy,
                )

            applied_change = True

        # Remove remaining policy references which no longer exist in blueprint
        for existing_ref in existing_policy_refs.values():
            if existing_ref["object_type"] == ObjectType.ACCOUNT.name:
                self.engine.execute_unsafe_ddl(
                    "ALTER ACCOUNT UNSET AUTHENTICATION POLICY",
                    condition=self.engine.settings.execute_authentication_policy
                    and self.engine.settings.execute_account_level_policy,
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {object_name:i} UNSET AUTHENTICATION POLICY",
                    {
                        "object_type": existing_ref["object_type"],
                        "object_name": existing_ref["name"],
                    },
                    condition=self.engine.settings.execute_authentication_policy,
                )

            applied_change = True

        return applied_change

    def _drop_policy_refs(self, policy_name: SchemaObjectIdent):
        existing_policy_refs = self._get_existing_policy_refs(policy_name)

        for existing_ref in existing_policy_refs.values():
            if existing_ref["object_type"] == ObjectType.ACCOUNT.name:
                self.engine.execute_unsafe_ddl(
                    "ALTER ACCOUNT UNSET AUTHENTICATION POLICY",
                    condition=self.engine.settings.execute_authentication_policy
                    and self.engine.settings.execute_account_level_policy,
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {object_name:i} UNSET AUTHENTICATION POLICY",
                    {
                        "object_type": existing_ref["object_type"],
                        "object_name": existing_ref["name"],
                    },
                    condition=self.engine.settings.execute_authentication_policy,
                )

    def _get_existing_policy_refs(self, policy_name: SchemaObjectIdent):
        existing_policy_refs = {}

        cur = self.engine.execute_meta(
            "SELECT * FROM TABLE(snowflake.information_schema.policy_references(policy_name => {policy_name}))",
            {
                "policy_name": policy_name,
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
