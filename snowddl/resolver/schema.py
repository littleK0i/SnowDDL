from snowddl.blueprint import SchemaBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType, SnowDDLUnsupportedError


class SchemaResolver(AbstractResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.SCHEMA

    def get_existing_objects(self):
        return self.engine.schema_cache.schemas

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(SchemaBlueprint)

    def create_object(self, bp: SchemaBlueprint):
        query = self.engine.query_builder()
        query.append("CREATE")

        if bp.is_transient:
            query.append("TRANSIENT")

        query.append("SCHEMA {database:i}.{schema:i}", {
            "database": bp.database,
            "schema": bp.schema,
        })

        query.append_nl("WITH MANAGED ACCESS")

        if bp.retention_time is not None:
            query.append_nl("DATA_RETENTION_TIME_IN_DAYS = {retention_time:d}", {
                "retention_time": bp.retention_time
            })

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        self.engine.execute_safe_ddl(query)

        return ResolveResult.CREATE

    def compare_object(self, bp: SchemaBlueprint, row: dict):
        if bp.is_transient != row['is_transient']:
            if bp.is_transient:
                raise SnowDDLUnsupportedError("Cannot change PERMANENT object into TRANSIENT object")
            else:
                raise SnowDDLUnsupportedError("Cannot change TRANSIENT object into PERMANENT object")

        query = self.engine.query_builder()

        query.append("ALTER SCHEMA {database:i}.{schema:i} SET ", {
            "database": bp.database,
            "schema": bp.schema,
        })

        if bp.retention_time is not None and bp.retention_time != row['retention_time']:
            query.append_nl("DATA_RETENTION_TIME_IN_DAYS = {retention_time:d}", {
                "retention_time": bp.retention_time
            })

        if bp.comment != row['comment']:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment
            })

        if query.fragment_count() > 1:
            self.engine.execute_unsafe_ddl(query)
            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl("DROP SCHEMA {database:i}.{schema:i}", {
            "database": row['database'],
            "schema": row['schema'],
        })

        return ResolveResult.DROP

    def _post_process(self):
        for result, object_names in self.resolved_objects.items():
            if len(object_names) == 0 or result == ResolveResult.NOCHANGE:
                continue

            # Reload cache if at least one object was changed
            self.engine.schema_cache.reload()
            return
