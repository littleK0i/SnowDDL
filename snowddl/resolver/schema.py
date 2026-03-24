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

        query.append("SCHEMA {full_name:i}", {"full_name": bp.full_name})

        if self.config.get_permission_model(bp.permission_model).ruleset.create_managed_access_schema:
            query.append_nl("WITH MANAGED ACCESS")

        if bp.retention_time is not None:
            query.append_nl("DATA_RETENTION_TIME_IN_DAYS = {retention_time:d}", {"retention_time": bp.retention_time})

        if bp.external_volume:
            query.append_nl("EXTERNAL_VOLUME = {external_volume:i}", {"external_volume": bp.external_volume})

        if bp.catalog:
            query.append_nl("CATALOG = {catalog:i}", {"catalog": bp.catalog})

        if bp.catalog_sync:
            query.append_nl("CATALOG_SYNC = {catalog_sync:i}", {"catalog_sync": bp.catalog_sync})

        if bp.log_level:
            query.append_nl("LOG_LEVEL = {log_level}", {"log_level": bp.log_level})

        if bp.log_event_level:
            query.append_nl("LOG_EVENT_LEVEL = {log_event_level}", {"log_event_level": bp.log_event_level})

        if bp.metric_level:
            query.append_nl("METRIC_LEVEL = {metric_level}", {"metric_level": bp.metric_level})

        if bp.trace_level:
            query.append_nl("TRACE_LEVEL = {trace_level}", {"trace_level": bp.trace_level})

        if bp.quoted_identifiers_ignore_case:
            query.append_nl(
                "QUOTED_IDENTIFIERS_IGNORE_CASE = {quoted_identifiers_ignore_case:b}",
                {
                    "quoted_identifiers_ignore_case": bp.quoted_identifiers_ignore_case
                }
            )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        self.engine.execute_safe_ddl(query)

        return ResolveResult.CREATE

    def compare_object(self, bp: SchemaBlueprint, row: dict):
        result = ResolveResult.NOCHANGE
        schema_params = self.engine.schema_cache.schema_params[str(bp.full_name)]

        if bp.is_transient != row["is_transient"]:
            if bp.is_transient:
                raise SnowDDLUnsupportedError(f"Cannot change PERMANENT schema [{bp.full_name}] into TRANSIENT schema")
            else:
                raise SnowDDLUnsupportedError(f"Cannot change TRANSIENT schema [{bp.full_name}] into PERMANENT schema")

        if bp.retention_time is not None and bp.retention_time != row["retention_time"]:
            self.engine.execute_unsafe_ddl(
                "ALTER SCHEMA {full_name:i} SET DATA_RETENTION_TIME_IN_DAYS = {retention_time:d}",
                {
                    "full_name": bp.full_name,
                    "retention_time": bp.retention_time,
                }
            )

            result = ResolveResult.ALTER

        if bp.external_volume != schema_params.get("EXTERNAL_VOLUME"):
            if bp.external_volume:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} SET EXTERNAL_VOLUME = {external_volume:i}",
                    {
                        "full_name": bp.full_name,
                        "external_volume": bp.external_volume,
                    }
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} UNSET EXTERNAL_VOLUME",
                    {
                        "full_name": bp.full_name,
                    }
                )

            result = ResolveResult.ALTER

        if bp.catalog != schema_params.get("CATALOG"):
            if bp.catalog:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} SET CATALOG = {catalog:i}",
                    {
                        "full_name": bp.full_name,
                        "catalog": bp.catalog,
                    }
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} UNSET CATALOG",
                    {
                        "full_name": bp.full_name,
                    }
                )

            result = ResolveResult.ALTER

        if bp.catalog_sync != schema_params.get("CATALOG_SYNC"):
            if bp.catalog_sync:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} SET CATALOG_SYNC = {catalog_sync:i}",
                    {
                        "full_name": bp.full_name,
                        "catalog_sync": bp.catalog_sync,
                    }
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} UNSET CATALOG_SYNC",
                    {
                        "full_name": bp.full_name,
                    }
                )

            result = ResolveResult.ALTER

        if bp.log_level != schema_params.get("LOG_LEVEL"):
            if bp.log_level:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} SET LOG_LEVEL = {log_level}",
                    {
                        "full_name": bp.full_name,
                        "log_level": bp.log_level,
                    },
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} UNSET LOG_LEVEL",
                    {
                        "full_name": bp.full_name,
                    },
                )

            result = ResolveResult.ALTER

        if bp.log_event_level != schema_params.get("LOG_EVENT_LEVEL"):
            if bp.log_event_level:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} SET LOG_EVENT_LEVEL = {log_event_level}",
                    {
                        "full_name": bp.full_name,
                        "log_event_level": bp.log_event_level,
                    },
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} UNSET LOG_EVENT_LEVEL",
                    {
                        "full_name": bp.full_name,
                    },
                )

            result = ResolveResult.ALTER

        if bp.metric_level != schema_params.get("METRIC_LEVEL"):
            if bp.metric_level:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} SET METRIC_LEVEL = {metric_level}",
                    {
                        "full_name": bp.full_name,
                        "metric_level": bp.metric_level,
                    },
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} UNSET METRIC_LEVEL",
                    {
                        "full_name": bp.full_name,
                    },
                )

            result = ResolveResult.ALTER

        if bp.trace_level != schema_params.get("TRACE_LEVEL"):
            if bp.trace_level:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} SET TRACE_LEVEL = {trace_level}",
                    {
                        "full_name": bp.full_name,
                        "trace_level": bp.trace_level,
                    },
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} UNSET TRACE_LEVEL",
                    {
                        "full_name": bp.full_name,
                    },
                )

            result = ResolveResult.ALTER

        if bp.quoted_identifiers_ignore_case != schema_params.get("QUOTED_IDENTIFIERS_IGNORE_CASE"):
            if bp.quoted_identifiers_ignore_case is not None:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} SET QUOTED_IDENTIFIERS_IGNORE_CASE = {quoted_identifiers_ignore_case:b}",
                    {
                        "full_name": bp.full_name,
                        "quoted_identifiers_ignore_case": bp.quoted_identifiers_ignore_case,
                    },
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER SCHEMA {full_name:i} UNSET QUOTED_IDENTIFIERS_IGNORE_CASE",
                    {
                        "full_name": bp.full_name,
                    },
                )

            result = ResolveResult.ALTER

        if bp.comment != row["comment"]:
            self.engine.execute_unsafe_ddl(
                "ALTER SCHEMA {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
            )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP SCHEMA {database:i}.{schema:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
            },
        )

        return ResolveResult.DROP

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

            # Parent object is going to be dropped
            if self.engine.intention_cache.check_parent_object_drop_intention(self.object_type, schema_full_name):
                continue

            database_full_name = ".".join(schema_full_name.split(".")[:1])
            database_bp = self.config.get_blueprints_by_type(DatabaseBlueprint).get(database_full_name)

            # Schema database does not exist in blueprints, schema will be dropped automatically on DROP DATABASE
            if database_bp is None:
                continue

            # Schemas without blueprints are allowed in sandbox databases, should not be dropped
            if database_bp.is_sandbox:
                continue

            tasks[schema_full_name] = (self.drop_object, self.existing_objects[schema_full_name])

        self._process_tasks(tasks)
