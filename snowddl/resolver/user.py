from base64 import b64encode, b64decode
from hashlib import sha256

from snowddl.blueprint import UserBlueprint
from snowddl.error import SnowDDLExecuteError
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType
from snowddl.resolver._utils import compare_dynamic_param_value


class UserResolver(AbstractResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.USER

    def get_existing_objects(self):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW USERS LIKE {env_prefix:ls}", {
            'env_prefix': self.config.env_prefix,
        })

        for r in cur:
            if r['owner'] != self.engine.context.current_role:
                continue

            existing_objects[r['name']] = {
                "name": r['name'],
                "login_name": r['login_name'] if r['login_name'] else None,
                "display_name": r['display_name'] if r['display_name'] else None,
                "first_name": r['first_name'] if r['first_name'] else None,
                "last_name": r['last_name'] if r['last_name'] else None,
                "email": r['email'] if r['email'] else None,
                "disabled": r['disabled'] == 'true',
                "default_warehouse": r['default_warehouse'] if r['default_warehouse'] else None,
                "default_namespace": r['default_namespace'] if r['default_namespace'] else None,
                "default_role": r['default_role'] if r['default_role'] else None,
                "has_password": r['has_password'] == 'true',
                "has_rsa_public_key": r['has_rsa_public_key'] == 'true',
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(UserBlueprint)

    def create_object(self, bp: UserBlueprint):
        query = self.engine.query_builder()

        query.append("CREATE USER {name:i}", {
            "name": bp.full_name,
        })

        if bp.password:
            query.append_nl("PASSWORD = {password}", {
                "password": bp.password,
            })

        if bp.rsa_public_key:
            query.append_nl("RSA_PUBLIC_KEY = {rsa_public_key}", {
                "rsa_public_key": bp.rsa_public_key,
            })

        if bp.rsa_public_key_2:
            query.append_nl("RSA_PUBLIC_KEY_2 = {rsa_public_key_2}", {
                "rsa_public_key_2": bp.rsa_public_key_2,
            })

        query.append(self._build_common_properties(bp))
        query.append(self._build_common_parameters(bp))

        self.engine.execute_safe_ddl(query)

        self.engine.execute_safe_ddl("GRANT ROLE {user_role:i} TO USER {user_name:i}", {
            "user_name": bp.full_name,
            "user_role": self._get_user_role_ident(bp),
        })

        return ResolveResult.CREATE

    def compare_object(self, bp: UserBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if self._compare_properties(bp, row):
            result = ResolveResult.ALTER

        if self._compare_public_keys(bp, row):
            result = ResolveResult.ALTER

        if self._compare_parameters(bp):
            result = ResolveResult.ALTER

        if self.engine.settings.refresh_user_passwords and self._refresh_password(bp, row):
            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl("DROP USER {name:i}", {
            "name": row['name'],
        })

        return ResolveResult.DROP

    def _build_common_properties(self, bp: UserBlueprint):
        query = self.engine.query_builder()

        query.append_nl("DISABLED = {disabled:b}", {"disabled": bp.disabled})
        query.append_nl("FIRST_NAME = {first_name}", {"first_name": bp.first_name})
        query.append_nl("LAST_NAME = {last_name}", {"last_name": bp.last_name})
        query.append_nl("EMAIL = {email}", {"email": bp.email})

        query.append_nl("DEFAULT_WAREHOUSE = {default_warehouse}", {"default_warehouse": bp.default_warehouse})
        query.append_nl("DEFAULT_NAMESPACE = {default_namespace}", {"default_namespace": bp.default_namespace})

        query.append_nl("DEFAULT_ROLE = {default_role:i}", {"default_role": self._get_user_role_ident(bp)})

        return query

    def _build_common_parameters(self, bp: UserBlueprint):
        query = self.engine.query_builder()

        for param_name, param_value in bp.session_params.items():
            query.append_nl("{param_name:r} = {param_value:dp}", {
                "param_name": param_name,
                "param_value": param_value,
            })

        return query

    def _compare_properties(self, bp: UserBlueprint, row: dict):
        if bp.first_name == row['first_name'] \
        and bp.last_name == row['last_name'] \
        and bp.email == row['email'] \
        and bp.disabled == row['disabled'] \
        and ((bp.default_warehouse is None and row['default_warehouse'] is None) or str(bp.default_warehouse) == row['default_warehouse']) \
        and ((bp.default_namespace is None and row['default_namespace'] is None) or str(bp.default_namespace) == row['default_namespace']) \
        and str(self._get_user_role_ident(bp)) == row['default_role']:
            return False

        query = self.engine.query_builder()

        query.append("ALTER USER {name:i} SET", {
            "name": bp.full_name,
        })

        query.append(self._build_common_properties(bp))

        self.engine.execute_safe_ddl(query)

        return True

    def _compare_public_keys(self, bp: UserBlueprint, row: dict):
        if not bp.rsa_public_key and not bp.rsa_public_key_2 and not row['has_rsa_public_key']:
            return False

        existing_public_key_fp = None
        existing_public_key_2_fp = None

        cur = self.engine.execute_meta("DESC USER {name:i}", {
            "name": bp.full_name,
        })

        for r in cur:
            if r['property'] == 'RSA_PUBLIC_KEY_FP' and r['value'] != 'null':
                existing_public_key_fp = r['value']

            if r['property'] == 'RSA_PUBLIC_KEY_2_FP' and r['value'] != 'null':
                existing_public_key_2_fp = r['value']

        if self._get_public_key_fingerprint(bp.rsa_public_key) == existing_public_key_fp \
        and self._get_public_key_fingerprint(bp.rsa_public_key_2) == existing_public_key_2_fp:
            return False

        self.engine.execute_safe_ddl("ALTER USER {name:i} SET rsa_public_key = {rsa_public_key}, rsa_public_key_2={rsa_public_key_2}", {
            "name": bp.full_name,
            "rsa_public_key": bp.rsa_public_key,
            "rsa_public_key_2": bp.rsa_public_key_2,
        })

        return True

    def _compare_parameters(self, bp: UserBlueprint):
        existing_params = self._get_existing_user_parameters(bp)
        query = self.engine.query_builder()

        query.append("ALTER USER {name:i} SET", {
            "name": bp.full_name,
        })

        for param_name, param_value in bp.session_params.items():
            if param_name not in existing_params:
                raise ValueError(f"Unknown parameter [{param_name}] for user [{bp.full_name}]")

            if compare_dynamic_param_value(param_value, existing_params[param_name]['value']):
                continue

            # At least one parameter in blueprint does not match the existing value
            # Refresh all parameters for such user
            query.append(self._build_common_parameters(bp))
            break

        # If parameter was set on USER level and does not exist in blueprint anymore
        # Unset such parameter and reset it to default
        for param_name, p in existing_params.items():
            if p['level'] == 'USER' and p['key'] not in bp.session_params:
                # Setting parameter to NULL equals to UNSET
                query.append_nl("{param_name:r} = NULL", {
                    "param_name": param_name,
                })

        if query.fragment_count() > 1:
            self.engine.execute_safe_ddl(query)
            return True

        return False

    def _refresh_password(self, bp: UserBlueprint, row: dict):
        if bp.password:
            try:
                self.engine.execute_safe_ddl("ALTER USER {name:i} SET PASSWORD = {password}", {
                    "name": bp.full_name,
                    "password": bp.password,
                })
            except SnowDDLExecuteError as e:
                # Password rejected due to 'PRIOR_USE'
                # Not a error, skip such user
                if e.snow_exc.errno == 3002:
                    return False
                else:
                    raise

            return True

        if row['has_password']:
            self.engine.execute_safe_ddl("ALTER USER {name:i} UNSET PASSWORD", {
                "name": bp.full_name,
            })

            return True

        return False

    def _get_user_role_ident(self, bp: UserBlueprint):
        return self.config.build_role_ident(bp.full_name, self.config.USER_ROLE_SUFFIX)

    def _get_public_key_fingerprint(self, rsa_public_key):
        if rsa_public_key is None:
            return None

        sha256hash = sha256()
        sha256hash.update(b64decode(rsa_public_key))

        return f"SHA256:{b64encode(sha256hash.digest()).decode('utf-8')}"

    def _get_existing_user_parameters(self, bp: UserBlueprint):
        existing_params = {}

        cur = self.engine.execute_meta("SHOW PARAMETERS IN USER {name:i}", {
            "name": bp.full_name,
        })

        for r in cur:
            existing_params[r['key']] = r

        return existing_params
