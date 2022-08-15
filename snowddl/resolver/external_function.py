from snowddl.blueprint import ExternalFunctionBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType
from snowddl.resolver._utils import dtypes_from_arguments


class ExternalFunctionResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.EXTERNAL_FUNCTION

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW EXTERNAL FUNCTIONS IN SCHEMA {database:i}.{schema:i}", {
            "database": schema['database'],
            "schema": schema['schema'],
        })

        for r in cur:
            full_name = f"{r['catalog_name']}.{r['schema_name']}.{r['name']}({dtypes_from_arguments(r['arguments'])})"

            existing_objects[full_name] = {
                "database": r['catalog_name'],
                "schema": r['schema_name'],
                "name": r['name'],
                "arguments": r['arguments'],
                "comment": r['description'],
                "is_secure": r['is_secure'] == 'Y',
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(ExternalFunctionBlueprint)

    def create_object(self, bp: ExternalFunctionBlueprint):
        query = self._build_create_function(bp)

        self.engine.execute_safe_ddl(query)

        self.engine.execute_safe_ddl("COMMENT ON FUNCTION {full_name:i} IS {comment}", {
            "full_name": bp.full_name,
            "comment": query.add_short_hash(bp.comment),
        })

        return ResolveResult.CREATE

    def compare_object(self, bp: ExternalFunctionBlueprint, row: dict):
        query = self._build_create_function(bp)

        if not query.compare_short_hash(row['comment']):
            self.engine.execute_safe_ddl(query)

            self.engine.execute_safe_ddl("COMMENT ON FUNCTION {full_name:i} IS {comment}", {
                "full_name": bp.full_name,
                "comment": query.add_short_hash(bp.comment),
            })

            return ResolveResult.REPLACE

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl("DROP FUNCTION {database:i}.{schema:i}.{name:i}({dtypes:r})", {
            "database": row['database'],
            "schema": row['schema'],
            "name": row['name'],
            "dtypes": dtypes_from_arguments(row['arguments']),
        })

        return ResolveResult.DROP

    def _build_create_function(self, bp: ExternalFunctionBlueprint):
        query = self.engine.query_builder()
        query.append("CREATE OR REPLACE")

        if bp.is_secure:
            query.append("SECURE")

        query.append("EXTERNAL FUNCTION {full_name:in} (", {
            "full_name": bp.full_name,
        })

        for idx, arg in enumerate(bp.arguments):
            query.append_nl("    {comma:r}{arg_name:i} {arg_type:r}", {
                "comma": "  " if idx == 0 else ", ",
                "arg_name": arg.name,
                "arg_type": arg.type,
            })

        query.append_nl(")")

        query.append_nl("RETURNS {ret_type:r}", {
            "ret_type": bp.returns,
        })

        query.append_nl("API_INTEGRATION = {api_integration:i}", {
            "api_integration": bp.api_integration,
        })

        if bp.is_strict:
            query.append_nl("STRICT")

        if bp.is_immutable:
            query.append_nl("IMMUTABLE")

        if bp.headers:
            query.append_nl("HEADERS = (")

            for idx, (header_name, header_value) in enumerate(bp.headers.items()):
                query.append_nl("    {comma:r}{header_name} = {header_value}", {
                    "comma": "  " if idx == 0 else ", ",
                    "header_name": header_name,
                    "header_value": header_value,
                })

            query.append_nl(")")

        if bp.context_headers:
            query.append_nl("CONTEXT_HEADERS = ({context_headers:r})", {
                "context_headers": bp.context_headers,
            })

        if bp.max_batch_rows:
            query.append_nl("MAX_BATCH_ROWS = {max_batch_rows:d}", {
                "max_batch_rows": bp.max_batch_rows,
            })

        if bp.compression:
            query.append_nl("COMPRESSION = {compression}", {
                "compression": bp.compression,
            })

        if bp.request_translator:
            query.append_nl("REQUEST_TRANSLATOR = {request_translator:i}", {
                "request_translator": bp.request_translator,
            })

        if bp.response_translator:
            query.append_nl("RESPONSE_TRANSLATOR = {response_translator:i}", {
                "response_translator": bp.response_translator,
            })

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        query.append_nl("AS {url}", {
            "url": bp.url,
        })

        return query
