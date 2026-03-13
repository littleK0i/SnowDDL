from snowddl.blueprint import DatabaseBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class DatabaseDelayedResolver(AbstractResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.DATABASE

    def get_existing_objects(self):
        return self.engine.schema_cache.databases

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(DatabaseBlueprint)

    def create_object(self, bp: DatabaseBlueprint):
        result = ResolveResult.NOCHANGE

        if bp.event_table:
            self.engine.execute_unsafe_ddl(
                "ALTER DATABASE {full_name:i} SET EVENT_TABLE = {event_table}",
                {
                    "full_name": bp.full_name,
                    "event_table": bp.event_table,
                },
                condition=self.engine.context.is_account_admin
            )

            result = ResolveResult.ALTER

        return result

    def compare_object(self, bp: DatabaseBlueprint, row: dict):
        result = ResolveResult.NOCHANGE
        database_params = self.engine.schema_cache.database_params[str(bp.full_name)]

        if bp.event_table != database_params.get("EVENT_TABLE"):
            if bp.event_table:
                self.engine.execute_unsafe_ddl(
                    "ALTER DATABASE {full_name:i} SET EVENT_TABLE = {event_table}",
                    {
                        "full_name": bp.full_name,
                        "event_table": bp.event_table,
                    },
                    condition=self.engine.context.is_account_admin
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER DATABASE {full_name:i} UNSET EVENT_TABLE",
                    {
                        "full_name": bp.full_name,
                    },
                    condition=self.engine.context.is_account_admin
                )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        return ResolveResult.NOCHANGE
