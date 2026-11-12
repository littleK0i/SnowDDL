from json import loads
from yaml import safe_dump

from snowddl.blueprint import AbstractIdent, McpServerBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class McpServerResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.MCP_SERVER

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW MCP SERVERS IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "owner": r["owner"],
                "comment": r["comment"],
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(McpServerBlueprint)

    def create_object(self, bp: McpServerBlueprint):
        self.engine.execute_unsafe_ddl(self._build_create_mcp_server(bp))

        return ResolveResult.CREATE

    def compare_object(self, bp: McpServerBlueprint, row: dict):
        cur = self.engine.execute_meta("DESC MCP SERVER {full_name:i}", {"full_name": bp.full_name})
        r = cur.fetchone()

        is_replace_required = False

        if bp.specification != loads(r["server_spec"]):
            is_replace_required = True

        if bp.comment != row["comment"]:
            is_replace_required = True

        if is_replace_required:
            self.engine.execute_unsafe_ddl(self._build_create_mcp_server(bp))
            return ResolveResult.REPLACE

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP MCP SERVER {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_create_mcp_server(self, bp: McpServerBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE OR REPLACE MCP SERVER {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        query.append_nl(
            "FROM SPECIFICATION {specification}",
            {
                "specification": "\n" + safe_dump(self._ident_to_str_recursive(bp.specification), sort_keys=False),
            },
        )

        return query

    def _ident_to_str_recursive(self, val):
        if isinstance(val, AbstractIdent):
            return str(val)

        if isinstance(val, (list, tuple, set)):
            return [self._ident_to_str_recursive(item) for item in val]

        if isinstance(val, dict):
            return {key: self._ident_to_str_recursive(item) for key, item in val.items()}

        return val
