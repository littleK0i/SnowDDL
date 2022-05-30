from snowddl.blueprint import DatabaseBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType, SnowDDLUnsupportedError


class DatabaseResolver(AbstractResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.DATABASE

    def get_existing_objects(self):
        return self.engine.schema_cache.databases

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(DatabaseBlueprint)

    def create_object(self, bp: DatabaseBlueprint):
        query = self.engine.query_builder()
        query.append("CREATE")

        if bp.is_transient:
            query.append("TRANSIENT")

        query.append("DATABASE {full_name:i}", {
            "full_name": bp.full_name,
        })

        if bp.retention_time is not None:
            query.append_nl("DATA_RETENTION_TIME_IN_DAYS = {retention_time:d}", {
                "retention_time": bp.retention_time
            })

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        self.engine.execute_safe_ddl(query)

        # Drop schema PUBLIC which is created automatically
        self.engine.execute_safe_ddl("DROP SCHEMA {database:i}.{schema:i}", {
            "database": bp.full_name,
            "schema": "PUBLIC"
        })

        return ResolveResult.CREATE

    def compare_object(self, bp: DatabaseBlueprint, row: dict):
        if bp.is_transient != row['is_transient']:
            if bp.is_transient:
                raise SnowDDLUnsupportedError("Cannot change PERMANENT object into TRANSIENT object")
            else:
                raise SnowDDLUnsupportedError("Cannot change TRANSIENT object into PERMANENT object")

        query = self.engine.query_builder()

        query.append("ALTER DATABASE {full_name:i} SET ", {
            "full_name": bp.full_name
        })

        if bp.retention_time is not None and bp.retention_time != row['retention_time']:
            query.append_nl("DATA_RETENTION_TIME_IN_DAYS = {retention_time:d}", {
                "retention_time": bp.retention_time
            })

        if bp.comment != row['comment']:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        if query.fragment_count() > 1:
            self.engine.execute_unsafe_ddl(query)
            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl("DROP DATABASE {database:i}", {
            "database": row['database']
        })

        return ResolveResult.DROP

    def _post_process(self):
        for result in self.resolved_objects.values():
            if result != ResolveResult.NOCHANGE:
                # Reload cache if at least one object was changed
                self.engine.schema_cache.reload()
                break
