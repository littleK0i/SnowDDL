from typing import Dict, Optional

from snowddl.blueprint.ident import SchemaObjectIdent
from snowddl.model import BaseModelWithConfig

MCP_SERVER_TOOL_TYPES = (
    "CORTEX_SEARCH_SERVICE_QUERY",
    "CORTEX_ANALYST_MESSAGE",
    "SYSTEM_EXECUTE_SQL",
    "CORTEX_AGENT_RUN",
    "GENERIC",
    "CODING_AGENT",
)


class McpServerTool(BaseModelWithConfig):
    name: str
    type: str
    title: str
    description: str
    identifier: Optional[SchemaObjectIdent] = None
    config: Optional[Dict] = None
    annotations: Optional[Dict[str, bool]] = None

    def to_specification(self):
        specification = self.model_dump(exclude_none=True)
        if self.identifier is not None:
            specification["identifier"] = str(self.identifier)
        if self.type == "GENERIC" and "warehouse" in (self.config or {}):
            specification["config"]["warehouse"] = str(self.config["warehouse"])
        return specification
