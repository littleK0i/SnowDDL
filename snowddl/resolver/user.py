from snowddl.blueprint import UserBlueprint, build_role_ident
from snowddl.error import SnowDDLExecuteError
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType
from snowddl.resolver._utils import compare_dynamic_param_value


class UserResolver(AbstractResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.USER

    def get_existing_objects(self):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW USERS LIKE {env_prefix:ls}",
            {
                "env_prefix": self.config.env_prefix,
            },
        )

        for r in cur:
            if r["owner"] != self.engine.context.current_role:
                continue

            existing_objects[r["name"]] = {
                "name": r["name"],
                "login_name": r["login_name"] if r["login_name"] else None,
                "display_name": r["display_name"] if r["display_name"] else None,
                "first_name": r["first_name"] if r["first_name"] else None,
                "last_name": r["last_name"] if r["last_name"] else None,
                "email": r["email"] if r["email"] else None,
                "disabled": r["disabled"] == "true",
                "default_warehouse": r["default_warehouse"] if r["default_warehouse"] else None,
                "default_namespace": r["default_namespace"] if r["default_namespace"] else None,
                "default_role": r["default_role"] if r["default_role"] else None,
                "type": r["type"] if r["type"] else None,
                "has_password": r["has_password"] == "true",
                "has_rsa_public_key": r["has_rsa_public_key"] == "true",
                "has_mfa": r["has_mfa"] == "true",
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(UserBlueprint)

    def create_object(self, bp: UserBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE USER {name:i}",
            {
                "name": bp.full_name,
            },
        )

        # Common properties
        query.append_nl("LOGIN_NAME = {login_name}", {"login_name": bp.login_name})
        query.append_nl("DISPLAY_NAME = {display_name}", {"display_name": bp.display_name})

        if bp.disabled:
            query.append_nl("DISABLED = {disabled:b}", {"disabled": bp.disabled})

        if bp.first_name:
            query.append_nl("FIRST_NAME = {first_name}", {"first_name": bp.first_name})

        if bp.last_name:
            query.append_nl("LAST_NAME = {last_name}", {"last_name": bp.last_name})

        if bp.email:
            query.append_nl("EMAIL = {email}", {"email": bp.email})

        if bp.default_warehouse:
            query.append_nl("DEFAULT_WAREHOUSE = {default_warehouse}", {"default_warehouse": bp.default_warehouse})

        if bp.default_namespace:
            query.append_nl("DEFAULT_NAMESPACE = {default_namespace}", {"default_namespace": bp.default_namespace})

        query.append_nl("DEFAULT_ROLE = {default_role:i}", {"default_role": self._get_user_role_ident(bp)})

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {"comment": bp.comment})

        # Security properties
        if bp.password:
            query.append_nl("PASSWORD = {password}", {"password": bp.password})

        if bp.rsa_public_key:
            query.append_nl("RSA_PUBLIC_KEY = {rsa_public_key}", {"rsa_public_key": bp.rsa_public_key})

        if bp.rsa_public_key_2:
            query.append_nl("RSA_PUBLIC_KEY_2 = {rsa_public_key_2}", {"rsa_public_key_2": bp.rsa_public_key_2})

        # User type
        if bp.type:
            query.append_nl("TYPE = {type}", {"type": bp.type})

        # Object and session parameters
        query.append(self._build_common_parameters(bp))

        self.engine.execute_safe_ddl(query)

        self.engine.execute_safe_ddl(
            "GRANT ROLE {user_role:i} TO USER {user_name:i}",
            {
                "user_name": bp.full_name,
                "user_role": self._get_user_role_ident(bp),
            },
        )

        return ResolveResult.CREATE

    def compare_object(self, bp: UserBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if self._compare_properties(bp, row):
            result = ResolveResult.ALTER

        if self._compare_password(bp, row):
            result = ResolveResult.ALTER

        if self._compare_public_keys(bp, row):
            result = ResolveResult.ALTER

        if self._compare_type(bp, row):
            result = ResolveResult.ALTER

        if self._compare_parameters(bp):
            result = ResolveResult.ALTER

        if self._check_user_role_grant(bp):
            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP USER {name:i}",
            {
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_common_parameters(self, bp: UserBlueprint):
        query = self.engine.query_builder()

        for param_name, param_value in bp.session_params.items():
            query.append_nl(
                "{param_name:r} = {param_value:dp}",
                {
                    "param_name": param_name,
                    "param_value": param_value,
                },
            )

        return query

    def _compare_properties(self, bp: UserBlueprint, row: dict):
        query = self.engine.query_builder()

        query.append(
            "ALTER USER {name:i} SET",
            {
                "name": bp.full_name,
            },
        )

        if bp.login_name != row["login_name"]:
            query.append_nl("LOGIN_NAME = {login_name}", {"login_name": bp.login_name})

        if bp.display_name != row["display_name"]:
            query.append_nl("DISPLAY_NAME = {display_name}", {"display_name": bp.display_name})

        if bp.disabled != row["disabled"]:
            query.append_nl("DISABLED = {disabled:b}", {"disabled": bp.disabled})

        if bp.first_name != row["first_name"]:
            query.append_nl("FIRST_NAME = {first_name}", {"first_name": bp.first_name})

        if bp.last_name != row["last_name"]:
            query.append_nl("LAST_NAME = {last_name}", {"last_name": bp.last_name})

        if bp.email != row["email"]:
            query.append_nl("EMAIL = {email}", {"email": bp.email})

        if bp.default_warehouse != row["default_warehouse"]:
            query.append_nl("DEFAULT_WAREHOUSE = {default_warehouse}", {"default_warehouse": bp.default_warehouse})

        if bp.default_namespace != row["default_namespace"]:
            query.append_nl("DEFAULT_NAMESPACE = {default_namespace}", {"default_namespace": bp.default_namespace})

        if str(self._get_user_role_ident(bp)) != row["default_role"]:
            query.append_nl("DEFAULT_ROLE = {default_role:i}", {"default_role": self._get_user_role_ident(bp)})

        if bp.comment != row["comment"]:
            query.append_nl("COMMENT = {comment}", {"comment": bp.comment})

        if query.fragment_count() > 1:
            self.engine.execute_safe_ddl(query)
            return True

        return False

    def _compare_password(self, bp: UserBlueprint, row: dict):
        if bp.password and (not row["has_password"] or self.engine.settings.refresh_user_passwords):
            try:
                self.engine.execute_safe_ddl(
                    "ALTER USER {name:i} SET PASSWORD = {password}",
                    {
                        "name": bp.full_name,
                        "password": bp.password,
                    },
                )
            except SnowDDLExecuteError as e:
                # Password rejected due to 'PRIOR_USE'
                # Not an error, skip such user
                if e.snow_exc.errno == 3002:
                    return False
                else:
                    raise

            return True

        if not bp.password and row["has_password"]:
            self.engine.execute_safe_ddl(
                "ALTER USER {name:i} UNSET PASSWORD",
                {
                    "name": bp.full_name,
                },
            )

            return True

        return False

    def _compare_public_keys(self, bp: UserBlueprint, row: dict):
        if not bp.rsa_public_key and not bp.rsa_public_key_2 and not row["has_rsa_public_key"]:
            return False

        existing_public_key = None
        existing_public_key_2 = None

        cur = self.engine.execute_meta(
            "DESC USER {name:i}",
            {
                "name": bp.full_name,
            },
        )

        for r in cur:
            if r["property"] == "RSA_PUBLIC_KEY" and r["value"] != "null":
                existing_public_key = r["value"]

            if r["property"] == "RSA_PUBLIC_KEY_2" and r["value"] != "null":
                existing_public_key_2 = r["value"]

        if bp.rsa_public_key == existing_public_key and bp.rsa_public_key_2 == existing_public_key_2:
            return False

        query = self.engine.query_builder()

        query.append(
            "ALTER USER {name:i} SET",
            {
                "name": bp.full_name,
            },
        )

        query.append_nl("RSA_PUBLIC_KEY = {rsa_public_key}", {"rsa_public_key": bp.rsa_public_key})
        query.append_nl("RSA_PUBLIC_KEY_2 = {rsa_public_key_2}", {"rsa_public_key_2": bp.rsa_public_key_2})

        self.engine.execute_safe_ddl(query)

        return True

    def _compare_type(self, bp: UserBlueprint, row: dict):
        if bp.type != row["type"]:
            # Type is processed separately, since changing TYPE property impacts visibility of other properties
            self.engine.execute_safe_ddl(
                "ALTER USER {name:i} SET TYPE = {type}",
                {
                    "name": bp.full_name,
                    "type": bp.type,
                },
            )

            return True

        return False

    def _compare_parameters(self, bp: UserBlueprint):
        existing_params = self._get_existing_user_parameters(bp)
        query = self.engine.query_builder()

        query.append(
            "ALTER USER {name:i} SET",
            {
                "name": bp.full_name,
            },
        )

        for param_name, param_value in bp.session_params.items():
            if param_name not in existing_params:
                raise ValueError(f"Unknown parameter [{param_name}] for user [{bp.full_name}]")

            if compare_dynamic_param_value(param_value, existing_params[param_name]["value"]):
                continue

            # At least one parameter in blueprint does not match the existing value
            # Refresh all parameters for such user
            query.append(self._build_common_parameters(bp))
            break

        # If parameter was set on USER level and does not exist in blueprint anymore
        # Unset such parameter and reset it to default
        for param_name, p in existing_params.items():
            if p["level"] == "USER" and p["key"] not in bp.session_params:
                # Setting parameter to NULL equals to UNSET
                query.append_nl(
                    "{param_name:r} = NULL",
                    {
                        "param_name": param_name,
                    },
                )

        if query.fragment_count() > 1:
            self.engine.execute_safe_ddl(query)
            return True

        return False

    def _check_user_role_grant(self, bp: UserBlueprint):
        user_role = self._get_user_role_ident(bp)

        cur = self.engine.execute_meta(
            "SHOW GRANTS TO USER {name:i}",
            {
                "name": bp.full_name,
            },
        )

        for r in cur:
            if r["role"] == str(user_role):
                return False

        self.engine.execute_safe_ddl(
            "GRANT ROLE {user_role:i} TO USER {user_name:i}",
            {
                "user_name": bp.full_name,
                "user_role": user_role,
            },
        )

        return True

    def _get_user_role_ident(self, bp: UserBlueprint):
        return build_role_ident(self.config.env_prefix, bp.full_name.name, self.config.USER_ROLE_SUFFIX)

    def _get_existing_user_parameters(self, bp: UserBlueprint):
        existing_params = {}

        cur = self.engine.execute_meta(
            "SHOW PARAMETERS IN USER {name:i}",
            {
                "name": bp.full_name,
            },
        )

        for r in cur:
            # Network policy is managed via POLICY_REFERENCES in NetworkPolicyResolver
            if r["key"] == "NETWORK_POLICY":
                continue

            existing_params[r["key"]] = r

        return existing_params
