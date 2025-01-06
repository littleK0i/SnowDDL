from snowddl.blueprint import AuthenticationPolicyBlueprint, AuthenticationPolicyReference, ObjectType, SchemaObjectIdent
from snowddl.error import SnowDDLExecuteError
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

        if self._compare_policy(bp):
            result = ResolveResult.ALTER

        if self._apply_policy_refs(bp):
            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self._drop_policy_refs(SchemaObjectIdent("", row["database"], row["schema"], row["name"]))
        self._drop_policy(SchemaObjectIdent("", row["database"], row["schema"], row["name"]))

        return ResolveResult.DROP

    def _create_policy(self, bp: AuthenticationPolicyBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE AUTHENTICATION POLICY {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        query.append_nl(
            "AUTHENTICATION_METHODS = ({authentication_methods})",
            {
                "authentication_methods": bp.authentication_methods,
            },
        )

        query.append_nl(
            "MFA_AUTHENTICATION_METHODS = ({mfa_authentication_methods})",
            {
                "mfa_authentication_methods": bp.mfa_authentication_methods,
            },
        )

        query.append_nl(
            "MFA_ENROLLMENT = {mfa_enrollment}",
            {
                "mfa_enrollment": bp.mfa_enrollment,
            },
        )

        query.append_nl(
            "CLIENT_TYPES = ({client_types})",
            {
                "client_types": bp.client_types,
            },
        )

        query.append_nl(
            "SECURITY_INTEGRATIONS = ({security_integrations})",
            {
                "security_integrations": bp.security_integrations,
            },
        )

        query.append_nl(
            "COMMENT = {comment}",
            {
                "comment": bp.comment,
            },
        )

        self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_authentication_policy)

    def _compare_policy(self, bp: AuthenticationPolicyBlueprint):
        applied_change = False

        cur = self.engine.execute_meta(
            "DESC AUTHENTICATION POLICY {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        row = {
            "authentication_methods": None,
            "mfa_authentication_methods": None,
            "mfa_enrollment": None,
            "client_types": None,
            "security_integrations": None,
            "comment": None,
        }

        for r in cur:
            k = r["property"].lower()

            if k not in row:
                continue

            if k == "comment" and r["value"] == "null":
                row[k] = None
            elif r["value"].startswith("["):
                row[k] = r["value"].strip("[]").split(", ")
            else:
                row[k] = r["value"]

        if bp.authentication_methods != row["authentication_methods"]:
            self.engine.execute_unsafe_ddl(
                "ALTER AUTHENTICATION POLICY {full_name:i} SET AUTHENTICATION_METHODS = ({authentication_methods})",
                {
                    "full_name": bp.full_name,
                    "authentication_methods": bp.authentication_methods,
                },
                condition=self.engine.settings.execute_authentication_policy,
            )

            applied_change = True

        if bp.mfa_authentication_methods != row["mfa_authentication_methods"]:
            self.engine.execute_unsafe_ddl(
                "ALTER AUTHENTICATION POLICY {full_name:i} SET MFA_AUTHENTICATION_METHODS = ({mfa_authentication_methods})",
                {
                    "full_name": bp.full_name,
                    "mfa_authentication_methods": bp.mfa_authentication_methods,
                },
                condition=self.engine.settings.execute_authentication_policy,
            )

            applied_change = True

        if bp.mfa_enrollment != row["mfa_enrollment"]:
            self.engine.execute_unsafe_ddl(
                "ALTER AUTHENTICATION POLICY {full_name:i} SET MFA_ENROLLMENT = {mfa_enrollment}",
                {
                    "full_name": bp.full_name,
                    "mfa_enrollment": bp.mfa_enrollment,
                },
                condition=self.engine.settings.execute_authentication_policy,
            )

            applied_change = True

        if bp.client_types != row["client_types"]:
            self.engine.execute_unsafe_ddl(
                "ALTER AUTHENTICATION POLICY {full_name:i} SET CLIENT_TYPES = ({client_types})",
                {
                    "full_name": bp.full_name,
                    "client_types": bp.client_types,
                },
                condition=self.engine.settings.execute_authentication_policy,
            )

            applied_change = True

        if bp.security_integrations != row["security_integrations"]:
            self.engine.execute_unsafe_ddl(
                "ALTER AUTHENTICATION POLICY {full_name:i} SET SECURITY_INTEGRATIONS = ({security_integrations:i})",
                {
                    "full_name": bp.full_name,
                    "security_integrations": bp.security_integrations,
                },
                condition=self.engine.settings.execute_authentication_policy,
            )

            applied_change = True

        if bp.comment != row["comment"]:
            self.engine.execute_unsafe_ddl(
                "ALTER AUTHENTICATION POLICY {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
                condition=self.engine.settings.execute_authentication_policy,
            )

            applied_change = True

        return applied_change

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
                # Apply new policy for ACCOUNT
                if self._object_has_another_policy_ref(ref):
                    # FORCE is not supported, must unset existing policy first
                    self.engine.execute_unsafe_ddl(
                        "-- Previous policy must be removed before setting a new policy\n"
                        "ALTER ACCOUNT UNSET AUTHENTICATION POLICY",
                        condition=self.engine.settings.execute_authentication_policy
                        and self.engine.settings.execute_account_level_policy,
                    )

                self.engine.execute_unsafe_ddl(
                    "ALTER ACCOUNT SET AUTHENTICATION POLICY {policy_name:i}",
                    {
                        "policy_name": bp.full_name,
                    },
                    condition=self.engine.settings.execute_authentication_policy
                    and self.engine.settings.execute_account_level_policy,
                )
            else:
                # Apply new policy for USER (and other object types in future?)
                if self._object_has_another_policy_ref(ref):
                    # FORCE is not supported, must unset existing policy first
                    self.engine.execute_unsafe_ddl(
                        "-- Previous policy must be removed before setting a new policy\n"
                        "ALTER {object_type:r} {object_name:i} UNSET AUTHENTICATION POLICY",
                        {
                            "object_type": ref.object_type.name,
                            "object_name": ref.object_name,
                        },
                        condition=self.engine.settings.execute_authentication_policy,
                    )

                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {object_name:i} SET AUTHENTICATION POLICY {policy_name:i}",
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

    def _object_has_another_policy_ref(self, ref: AuthenticationPolicyReference):
        try:
            cur = self.engine.execute_meta(
                "SELECT * FROM TABLE(snowflake.information_schema.policy_references(ref_entity_domain => {object_type}, ref_entity_name  => {object_name}))",
                {
                    "object_type": ref.object_type.name,
                    "object_name": self.engine.context.current_account if ref.object_type == ObjectType.ACCOUNT else ref.object_name,
                },
            )
        except SnowDDLExecuteError as e:
            # User does not exist or not authorized
            # Skip this error during planning
            if e.snow_exc.errno == 2003:
                return False
            else:
                raise

        for r in cur:
            if r["POLICY_KIND"] == "AUTHENTICATION_POLICY":
                return True

        return False
