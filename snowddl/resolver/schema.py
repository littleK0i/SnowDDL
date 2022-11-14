from snowddl.blueprint import SchemaBlueprint, DatabaseBlueprint
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

        query.append("SCHEMA {full_name:i}", {
            "full_name": bp.full_name
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

        query.append("ALTER SCHEMA {full_name:i} SET ", {
            "full_name": bp.full_name,
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

    def destroy(self):
        # Do nothing, all schemas are dropped automatically on DROP DATABASE
        pass

    def _post_process(self):
        for result in self.resolved_objects.values():
            if result != ResolveResult.NOCHANGE:
                # Reload cache if at least one object was changed
                self.engine.schema_cache.reload()
                break

    def _resolve_drop(self):
        tasks = {}

        for schema_full_name in sorted(self.existing_objects):
            # Object exists in blueprints, should not be dropped
            if schema_full_name in self.blueprints:
                continue

            database_full_name = '.'.join(schema_full_name.split('.')[:1])
            database_bp = self.config.get_blueprints_by_type(DatabaseBlueprint).get(database_full_name)

            # Schema database does not exist in blueprints, schema will be dropped automatically on DROP DATABASE
            if database_bp is None:
                continue

            # Schemas without blueprints are allowed in sandbox databases, should not be dropped
            if database_bp.is_sandbox:
                continue

            tasks[schema_full_name] = (self.drop_object, self.existing_objects[schema_full_name])

        self._process_tasks(tasks)
