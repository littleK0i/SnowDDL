from jsonschema import Draft202012Validator

from snowddl.blueprint import AccountObjectIdent, McpServerBlueprint, McpServerTool, SchemaBlueprint
from snowddl.blueprint.mcp_server import MCP_SERVER_TOOL_TYPES
from snowddl.validator.abc_validator import AbstractValidator


class McpServerValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(McpServerBlueprint)

    def validate_blueprint(self, bp: McpServerBlueprint):
        if bp.full_name.parts_for_format()[1] is not None:
            raise ValueError(f"MCP server [{bp.full_name}] cannot include arguments")

        if str(bp.full_name.schema_full_name) not in self.config.get_blueprints_by_type(SchemaBlueprint):
            raise ValueError(f"MCP server [{bp.full_name}] belongs to undefined schema [{bp.full_name.schema_full_name}]")

        if bp.comment is not None:
            raise ValueError(f"Comments are not supported for MCP server [{bp.full_name}]")

        if not 1 <= len(bp.tools) <= 50:
            raise ValueError(f"MCP server [{bp.full_name}] must contain between 1 and 50 tools")

        names = set()
        for tool in bp.tools:
            for field in ("name", "title", "description"):
                if not getattr(tool, field).strip():
                    raise ValueError(f"MCP tool [{tool.name}] has an empty [{field}]")

            if tool.name in names:
                raise ValueError(f"Duplicate MCP tool name [{tool.name}] in server [{bp.full_name}]")
            names.add(tool.name)

            if tool.type not in MCP_SERVER_TOOL_TYPES:
                raise ValueError(f"Unsupported MCP tool type [{tool.type}] in server [{bp.full_name}]")

            if tool.type in ("CORTEX_SEARCH_SERVICE_QUERY", "CORTEX_ANALYST_MESSAGE", "CORTEX_AGENT_RUN", "GENERIC"):
                if tool.identifier is None:
                    raise ValueError(f"MCP tool [{tool.name}] requires an identifier")
            elif tool.identifier is not None:
                raise ValueError(f"MCP tool [{tool.name}] of type [{tool.type}] does not support an identifier")

            if tool.annotations is not None:
                if (
                    tool.type not in ("GENERIC", "CORTEX_AGENT_RUN")
                    or set(tool.annotations) - {"readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"}
                    or any(not isinstance(value, bool) for value in tool.annotations.values())
                ):
                    raise ValueError(f"Unsupported annotations for MCP tool [{tool.name}]")

            if tool.type == "GENERIC":
                self._validate_generic_tool(tool)
            elif tool.type == "CODING_AGENT":
                excluded = {"messages", "thread_id", "parent_message_id", "stream", "background", "origin_application"}
                if excluded.intersection(tool.config or {}):
                    raise ValueError(
                        f"MCP coding tool [{tool.name}] config cannot contain {sorted(excluded.intersection(tool.config))}"
                    )
            elif tool.config is not None:
                raise ValueError(f"MCP tool [{tool.name}] of type [{tool.type}] does not support config")

    def _validate_generic_tool(self, tool: McpServerTool):
        config = tool.config
        if config is None or not {"type", "warehouse", "input_schema"}.issubset(config):
            raise ValueError(f"MCP generic tool [{tool.name}] config requires type, warehouse, and input_schema")
        if config["type"] not in ("function", "procedure"):
            raise ValueError(f"MCP generic tool [{tool.name}] config.type must be function or procedure")
        if set(config) - {"type", "warehouse", "input_schema"}:
            raise ValueError(f"Unsupported config properties for MCP generic tool [{tool.name}]")
        if not isinstance(config["warehouse"], AccountObjectIdent):
            raise ValueError(f"MCP generic tool [{tool.name}] config.warehouse must be an AccountObjectIdent")
        if not isinstance(config["input_schema"], dict):
            raise ValueError(f"MCP generic tool [{tool.name}] config.input_schema must be a JSON schema object")
        Draft202012Validator.check_schema(config["input_schema"])
