from json import loads
from typing import TYPE_CHECKING

from snowddl.blueprint import AccountObjectIdent, Edition

if TYPE_CHECKING:
    from snowddl.engine import SnowDDLEngine


class SnowDDLContext:
    def __init__(self, engine: "SnowDDLEngine"):
        self.engine = engine

        cur = self.engine.execute_meta(
            """
            SELECT CURRENT_ACCOUNT() AS current_account
                , CURRENT_REGION() AS current_region
                , CURRENT_SESSION() AS current_session
                , CURRENT_USER() AS current_user
                , CURRENT_ROLE() AS current_role
                , CURRENT_WAREHOUSE() AS current_warehouse
                , IS_ROLE_IN_SESSION('ACCOUNTADMIN') AS is_account_admin
                , IS_ROLE_IN_SESSION('SYSADMIN') AS is_sys_admin
                , IS_ROLE_IN_SESSION('SECURITYADMIN') AS is_security_admin
                , SYSTEM$BOOTSTRAP_DATA_REQUEST('ACCOUNT') AS bootstrap_account
        """
        )

        r = cur.fetchone()

        self.current_account = r["CURRENT_ACCOUNT"]
        self.current_region = r["CURRENT_REGION"]
        self.current_session = r["CURRENT_SESSION"]
        self.current_user = r["CURRENT_USER"]
        self.current_role = r["CURRENT_ROLE"]
        self.current_warehouse = r["CURRENT_WAREHOUSE"]

        self.original_role = self.current_role

        self.is_account_admin = r["IS_ACCOUNT_ADMIN"]
        self.is_sys_admin = r["IS_SYS_ADMIN"]
        self.is_security_admin = r["IS_SECURITY_ADMIN"]

        bootstrap_account = loads(r["BOOTSTRAP_ACCOUNT"])

        self.version = bootstrap_account["serverVersion"]
        self.edition = Edition[bootstrap_account["accountInfo"]["serviceLevelName"]]

        self._validate()

    def _validate(self):
        if not self.current_warehouse:
            if self.engine.settings.execute_replace_table:
                raise ValueError("Context error: missing CURRENT_WAREHOUSE in session to apply REPLACE TABLE")

        if not self.is_account_admin:
            if self.engine.settings.execute_account_params:
                raise ValueError("Context error: missing ACCOUNTADMIN role in session to apply ACCOUNT PARAMETERS")

            if self.engine.settings.execute_resource_monitor:
                raise ValueError("Context error: missing ACCOUNTADMIN role in session to apply RESOURCE MONITORS")

    def activate_role_with_prefix(self):
        if not self.engine.config.env_prefix:
            return

        role_with_prefix = AccountObjectIdent(self.engine.config.env_prefix, self.current_role)

        cur = self.engine.execute_meta("SHOW ROLES LIKE {role_with_prefix:lf}", {"role_with_prefix": role_with_prefix})

        if cur.rowcount == 0:
            self.engine.execute_context_ddl(
                "CREATE ROLE {role_with_prefix:i}",
                {
                    "role_with_prefix": role_with_prefix,
                },
            )

            self.engine.execute_context_ddl(
                "GRANT ROLE {current_role:i} TO ROLE {role_with_prefix:i}",
                {
                    "role_with_prefix": role_with_prefix,
                    "current_role": self.current_role,
                },
            )

            self.engine.execute_context_ddl(
                "GRANT ROLE {role_with_prefix:i} TO USER {current_user:i}",
                {
                    "role_with_prefix": role_with_prefix,
                    "current_user": self.current_user,
                },
            )

            if self.engine.settings.env_admin_role:
                self.engine.execute_context_ddl(
                    "GRANT ROLE {role_with_prefix:i} TO ROLE {env_admin_role:i}",
                    {
                        "role_with_prefix": role_with_prefix,
                        "env_admin_role": self.engine.settings.env_admin_role,
                    },
                )
            elif not self.is_account_admin:
                self.engine.execute_context_ddl(
                    "GRANT ROLE {role_with_prefix:i} TO ROLE ACCOUNTADMIN",
                    {
                        "role_with_prefix": role_with_prefix,
                    },
                )

        self.engine.execute_meta(
            "USE ROLE {role_with_prefix:i}",
            {
                "role_with_prefix": role_with_prefix,
            },
        )

        self.current_role = str(role_with_prefix)
        self.engine.flush_thread_buffers()

    def destroy_role_with_prefix(self):
        if not self.engine.config.env_prefix:
            return

        self.engine.execute_meta(
            "USE ROLE {original_role:i}",
            {
                "original_role": self.original_role,
            },
        )

        self.engine.execute_context_ddl(
            "DROP ROLE {role_with_prefix:i}",
            {
                "role_with_prefix": self.current_role,
            },
        )

        self.current_role = self.original_role
        self.engine.flush_thread_buffers()
