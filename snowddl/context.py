from typing import TYPE_CHECKING

from snowddl.blueprint import IdentWithPrefix, Edition

if TYPE_CHECKING:
    from snowddl.engine import SnowDDLEngine


class SnowDDLContext:
    def __init__(self, engine: "SnowDDLEngine"):
        self.engine = engine

        cur = self.engine.execute_meta("""
            SELECT CURRENT_SESSION() AS current_session
                , CURRENT_USER() AS current_user
                , CURRENT_ROLE() AS current_role
                , CURRENT_WAREHOUSE() AS current_warehouse
                , IS_ROLE_IN_SESSION('ACCOUNTADMIN') AS is_account_admin
                , IS_ROLE_IN_SESSION('SYSADMIN') AS is_sys_admin
                , IS_ROLE_IN_SESSION('SECURITYADMIN') AS is_security_admin
                , CURRENT_VERSION() AS version
        """)

        r = cur.fetchone()

        self.current_session = r['CURRENT_SESSION']
        self.current_user = r['CURRENT_USER']
        self.current_role = r['CURRENT_ROLE']
        self.current_warehouse = r['CURRENT_WAREHOUSE']

        self.is_account_admin = r['IS_ACCOUNT_ADMIN']
        self.is_sys_admin = r['IS_SYS_ADMIN']
        self.is_security_admin = r['IS_SECURITY_ADMIN']

        self.version = r['VERSION']
        self.edition = self._get_edition()

        self._validate()
        self._init_role_with_prefix()

        self.engine.flush_thread_buffers()

    def _get_edition(self):
        # TODO: discover a secret method to detect edition easier
        # Pattern is empty on purpose, we only need a structure of response
        description = self.engine.describe_meta("SHOW WAREHOUSES LIKE ''")

        for col in description:
            if col.name == 'min_cluster_count':
                return Edition.ENTERPRISE

        return Edition.STANDARD

    def _validate(self):
        if not self.current_warehouse:
            if self.engine.settings.execute_replace_table:
                raise ValueError("Context error: missing CURRENT_WAREHOUSE in session to apply REPLACE TABLE")

        if not self.is_account_admin:
            if self.engine.settings.execute_account_params:
                raise ValueError("Context error: missing ACCOUNTADMIN role in session to apply ACCOUNT PARAMETERS")

            if self.engine.settings.execute_resource_monitor:
                raise ValueError("Context error: missing ACCOUNTADMIN role in session to apply RESOURCE MONITORS")

    def _init_role_with_prefix(self):
        if not self.engine.config.env_prefix:
            return

        role_with_prefix = IdentWithPrefix(self.engine.config.env_prefix, self.current_role)

        cur = self.engine.execute_meta("SHOW ROLES LIKE {role_with_prefix:lf}", {
            "role_with_prefix": role_with_prefix
        })

        if cur.rowcount == 0:
            self.engine.execute_context_ddl("CREATE ROLE {role_with_prefix:i}", {
                "role_with_prefix": role_with_prefix,
            })

            self.engine.execute_context_ddl("GRANT ROLE {current_role:i} TO ROLE {role_with_prefix:i}", {
                "role_with_prefix": role_with_prefix,
                "current_role": self.current_role,
            })

            self.engine.execute_context_ddl("GRANT ROLE {role_with_prefix:i} TO USER {current_user:i}", {
                "role_with_prefix": role_with_prefix,
                "current_user": self.current_user,
            })

            self.engine.execute_context_ddl("GRANT ROLE {role_with_prefix:i} TO ROLE ACCOUNTADMIN", {
                "role_with_prefix": role_with_prefix,
                "current_role": self.current_role,
            })

        self.engine.execute_meta("USE ROLE {role_with_prefix:i}", {
            "role_with_prefix": role_with_prefix,
        })

        self.current_role = str(role_with_prefix)
