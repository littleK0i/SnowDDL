from copy import deepcopy

from snowddl.blueprint import (
    McpServerBlueprint,
    AccountObjectIdent,
    SchemaObjectIdent,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
mcp_server_json_schema = {
    "type": "object",
    "properties": {
        "specification": {
            "type": "object"
        },
        "comment": {
            "type": "string"
        }
    },
    "required": ["specification"],
    "additionalProperties": False
}
# fmt: on


class McpServerParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("mcp_server", mcp_server_json_schema, self.process_mcp_server)

    def process_mcp_server(self, f: ParsedFile):
        bp = McpServerBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            specification=self._normalize_specification(f),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)

    def _normalize_specification(self, f: ParsedFile):
        specification = deepcopy(f.params["specification"])

        if "version" not in specification:
            specification = {"version": 1} | specification

        if "tools" in specification:
            for t in specification["tools"]:
                if "type" in t:
                    t["type"] = t["type"].upper()

                if "identifier" in t:
                    t["identifier"] = build_schema_object_ident(self.env_prefix, t["identifier"], f.database, f.schema)

                if "global_identifier" in t:
                    parts = t["global_identifier"].split(".")

                    if len(parts) != 3:
                        raise ValueError(f"Invalid schema object identifier format in tool [{t['name']}], "
                                         f"expecting <database>.<schema>.<name>")

                    t["identifier"] = SchemaObjectIdent("", parts[0], parts[1], parts[2])
                    del t["global_identifier"]

                if "config" in t:
                    if "warehouse" in t["config"]:
                        t["config"]["warehouse"] = AccountObjectIdent(self.env_prefix, t["config"]["warehouse"])

                    if "global_warehouse" in t["config"]:
                        t["config"]["warehouse"] = AccountObjectIdent("", t["config"]["global_warehouse"])
                        del t["config"]["global_warehouse"]

        return specification
