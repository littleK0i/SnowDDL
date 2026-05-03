"""
Custom SnowDDL runner that prevents creation of users, warehouses, and databases.

These objects must be pre-created manually in Snowflake. SnowDDL will raise an
error if a YAML-defined object does not already exist, rather than creating it.
All other resolver behaviour (ALTER, DROP, role management) is unchanged.

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


class SkipCreateWarehouseResolver(WarehouseResolver):
    def create_object(self, bp):
        raise ValueError(
            f"Warehouse [{bp.full_name}] is defined in YAML config but does not exist in Snowflake. "
            f"Warehouses must be created manually before SnowDDL can manage their configuration."
        )


class SkipCreateDatabaseResolver(DatabaseResolver):
    def create_object(self, bp):
        raise ValueError(
            f"Database [{bp.full_name}] is defined in YAML config but does not exist in Snowflake. "
            f"Databases must be created manually before SnowDDL can manage their configuration."
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
