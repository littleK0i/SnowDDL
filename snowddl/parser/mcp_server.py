from functools import partial

from snowddl.blueprint import AccountObjectIdent, McpServerBlueprint, McpServerTool, SchemaObjectIdent, build_schema_object_ident
from snowddl.parser.abc_parser import AbstractParser

# fmt: off
mcp_server_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "tools": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "identifier": {"type": "string"},
                        "config": {"type": "object"},
                        "annotations": {
                            "type": "object",
                            "properties": {
                                "readOnlyHint": {"type": "boolean"},
                                "destructiveHint": {"type": "boolean"},
                                "idempotentHint": {"type": "boolean"},
                                "openWorldHint": {"type": "boolean"},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "required": ["name", "type", "title", "description"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["tools"],
        "additionalProperties": False,
    },
}
# fmt: on


class McpServerParser(AbstractParser):
    def load_blueprints(self):
        for database_name in self.get_database_names():
            for schema_name in self.get_schema_names_in_database(database_name):
                self.parse_multi_entity_file(
                    f"{database_name}/{schema_name}/mcp_server",
                    mcp_server_json_schema,
                    partial(self.process_mcp_server, database_name=database_name, schema_name=schema_name),
                )

    def process_mcp_server(self, server_name, server_params, database_name, schema_name):
        bp = McpServerBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, database_name, schema_name, server_name),
            tools=[self.build_tool(params, database_name, schema_name) for params in server_params["tools"]],
        )
        if str(bp.full_name) in self.config.get_blueprints_by_type(McpServerBlueprint):
            raise ValueError(f"Duplicate MCP server [{bp.full_name}]")
        self.config.add_blueprint(bp)

    def build_tool(self, params, database_name, schema_name):
        params = params.copy()
        if "identifier" in params:
            params["identifier"] = build_schema_object_ident(self.env_prefix, params["identifier"], database_name, schema_name)
        if params["type"] == "GENERIC" and "warehouse" in params.get("config", {}):
            params["config"] = params["config"].copy()
            params["config"]["warehouse"] = AccountObjectIdent(self.env_prefix, params["config"]["warehouse"])
        return McpServerTool(**params)
