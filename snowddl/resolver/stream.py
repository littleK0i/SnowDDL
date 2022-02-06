from snowddl.blueprint import StreamBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType
from snowddl.resolver._utils import coalesce

class StreamResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.STREAM

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW STREAMS IN SCHEMA {database:i}.{schema:i}", {
            "database": schema['database'],
            "schema": schema['schema'],
        })

        for r in cur:
            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r['database_name'],
                "schema": r['schema_name'],
                "name": r['name'],
                "object_name": r['table_name'],
                "type": r['type'],
                "mode": r['mode'],
                "comment": r['comment'] if r['comment'] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(StreamBlueprint)

    def create_object(self, bp: StreamBlueprint):
        query = self._build_create_stream_sql(bp)
        self.engine.execute_safe_ddl(query)

        return ResolveResult.CREATE

    def compare_object(self, bp: StreamBlueprint, row: dict):
        is_replace_required = False

        if coalesce(bp.append_only, False) != ('APPEND_ONLY' in row['mode']):
            is_replace_required = True

        if coalesce(bp.insert_only, False) != ('INSERT_ONLY' in row['mode']):
            is_replace_required = True

        if is_replace_required:
            query = self._build_create_stream_sql(bp, True)
            self.engine.execute_unsafe_ddl(query)

            return ResolveResult.REPLACE

        if bp.comment != row['comment']:
            self.engine.execute_safe_ddl("ALTER STREAM {full_name:i} SET COMMENT = {comment}", {
                "full_name": bp.full_name,
                "comment": bp.comment,
            })

            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl("DROP STREAM {database:i}.{schema:i}.{name:i}", {
            "database": row['database'],
            "schema": row['schema'],
            "name": row['name'],
        })

        return ResolveResult.DROP

    def _build_create_stream_sql(self, bp: StreamBlueprint, is_replace=False):
        query = self.engine.query_builder()
        query.append("CREATE")

        if is_replace:
            query.append("OR REPLACE")

        query.append("STREAM {full_name:i}", {
            "full_name": bp.full_name,
        })

        # TODO: uncomment when COPY GRANTS is supported for streams
        # https://docs.snowflake.com/en/sql-reference/sql/create-stream.html
        # query.append_nl("COPY GRANTS")

        query.append_nl("ON {object_type:r} {object_name:i}", {
            "object_type": bp.object_type.singular,
            "object_name": bp.object_name,
        })

        if bp.append_only is not None:
            query.append_nl("APPEND_ONLY = {append_only:b}", {
                "append_only": bp.append_only,
            })

        if bp.insert_only is not None:
            query.append_nl("INSERT_ONLY = {insert_only:b}", {
                "insert_only": bp.insert_only,
            })

        if bp.show_initial_rows is not None:
            query.append_nl("SHOW_INITIAL_ROWS = {show_initial_rows:b}", {
                "show_initial_rows": bp.show_initial_rows,
            })

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        return query
