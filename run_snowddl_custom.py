"""
Custom SnowDDL runner that prevents creation, alteration, and dropping of users,
warehouses, and databases.

These objects must be pre-created and managed manually in Snowflake. SnowDDL will
raise an error rather than CREATE or DROP any of them. For users, property changes
are silently skipped but the U_ROLE grant is still enforced on each run.

Usage: python run_snowddl_custom.py apply -c ./config --env-prefix DEV_
"""

from snowddl.app import BaseApp
from snowddl.resolver import default_resolve_sequence
from snowddl.resolver.user import UserResolver
from snowddl.resolver.warehouse import WarehouseResolver
from snowddl.resolver.database import DatabaseResolver
from snowddl.resolver.abc_resolver import ResolveResult


class SkipCreateUserResolver(UserResolver):
    def create_object(self, bp):
        raise ValueError(
            f"User [{bp.full_name}] is defined in YAML config but does not exist in Snowflake. "
            f"Users must be created manually before SnowDDL can manage their roles."
        )

    def compare_object(self, bp, row):
        self._check_user_role_grant(bp)
        return ResolveResult.NOCHANGE

    def drop_object(self, row):
        raise ValueError(
            f"User [{row['name']}] exists in Snowflake but is not defined in YAML config. "
            f"Users must be removed manually in Snowflake."
        )


class SkipCreateWarehouseResolver(WarehouseResolver):
    def create_object(self, bp):
        raise ValueError(
            f"Warehouse [{bp.full_name}] is defined in YAML config but does not exist in Snowflake. "
            f"Warehouses must be created manually before SnowDDL can manage their configuration."
        )

    def compare_object(self, bp, row):
        return ResolveResult.NOCHANGE

    def drop_object(self, row):
        raise ValueError(
            f"Warehouse [{row['name']}] exists in Snowflake but is not defined in YAML config. "
            f"Warehouses must be removed manually in Snowflake."
        )


class SkipCreateDatabaseResolver(DatabaseResolver):
    def create_object(self, bp):
        raise ValueError(
            f"Database [{bp.full_name}] is defined in YAML config but does not exist in Snowflake. "
            f"Databases must be created manually before SnowDDL can manage their configuration."
        )

    def compare_object(self, bp, row):
        return ResolveResult.NOCHANGE

    def drop_object(self, row):
        raise ValueError(
            f"Database [{row['database']}] exists in Snowflake but is not defined in YAML config. "
            f"Databases must be removed manually in Snowflake."
        )


_RESOLVER_OVERRIDES = {
    UserResolver: SkipCreateUserResolver,
    WarehouseResolver: SkipCreateWarehouseResolver,
    DatabaseResolver: SkipCreateDatabaseResolver,
}


class CustomApp(BaseApp):
    resolve_sequence = [
        _RESOLVER_OVERRIDES.get(cls, cls) for cls in default_resolve_sequence
    ]


if __name__ == "__main__":
    app = CustomApp()
    app.execute()
