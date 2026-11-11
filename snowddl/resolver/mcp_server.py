from copy import deepcopy
from json import loads

from yaml import safe_dump

from snowddl.blueprint import McpServerBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ObjectType, ResolveResult


class McpServerResolver(AbstractSchemaObjectResolver):
    # shortcut: removing the final declaration stops management; add explicit schema scope tracking for complete pruning.
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.MCP_SERVER

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(McpServerBlueprint)

    def get_existing_objects_in_schema(self, schema: dict):
        schema_name = f"{schema['database']}.{schema['schema']}"
        if not any(str(bp.full_name.schema_full_name) == schema_name for bp in self.get_blueprints().values()):
            return {}

        cur = self.engine.execute_meta(
            "SHOW MCP SERVERS IN SCHEMA {database:i}.{schema:i}",
            {"database": schema["database"], "schema": schema["schema"]},
        )
        return {
            f"{row['database_name']}.{row['schema_name']}.{row['name']}": {
                "database": row["database_name"],
                "schema": row["schema_name"],
                "name": row["name"],
                "owner": row["owner"],
            }
            for row in cur
        }

    def create_object(self, bp: McpServerBlueprint):
        self.engine.execute_safe_ddl(self._build_create_sql(bp))
        return ResolveResult.CREATE

    def compare_object(self, bp: McpServerBlueprint, row: dict):
        cur = self.engine.execute_meta("DESCRIBE MCP SERVER {full_name:i}", {"full_name": bp.full_name})
        existing = cur.fetchone()["server_spec"]
        if isinstance(existing, str):
            existing = loads(existing)
        desired = {"tools": [tool.to_specification() for tool in bp.tools]}

        if self._normalise_specification(existing) == self._normalise_specification(desired):
            return ResolveResult.NOCHANGE

        self.engine.execute_unsafe_ddl(self._build_create_sql(bp, replace=True))
        return ResolveResult.REPLACE

    def _build_create_sql(self, bp: McpServerBlueprint, replace=False):
        query = self.engine.query_builder()
        query.append(
            "{command:r} MCP SERVER {full_name:i} FROM SPECIFICATION {specification}",
            {
                "command": "CREATE OR REPLACE" if replace else "CREATE",
                "full_name": bp.full_name,
                "specification": safe_dump({"tools": [tool.to_specification() for tool in bp.tools]}, sort_keys=False),
            },
        )
        return query

    def _normalise_specification(self, specification):
        specification = deepcopy(specification)
        if specification.get("version") == 1:
            specification.pop("version")
        for tool in specification.get("tools", []):
            if tool["type"] in ("GENERIC", "CORTEX_AGENT_RUN"):
                tool["annotations"] = {
                    "readOnlyHint": False,
                    "destructiveHint": True,
                    "idempotentHint": False,
                    "openWorldHint": True,
                    **tool.get("annotations", {}),
                }
            if tool["type"] == "CODING_AGENT" and tool.get("config") == {}:
                tool.pop("config")
        if "tools" in specification:
            specification["tools"].sort(key=lambda tool: tool["name"])
        return specification

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP MCP SERVER {database:i}.{schema:i}.{name:i}",
            {"database": row["database"], "schema": row["schema"], "name": row["name"]},
        )
        return ResolveResult.DROP
