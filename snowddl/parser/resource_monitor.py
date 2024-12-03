from snowddl.blueprint import ResourceMonitorBlueprint, AccountObjectIdent
from snowddl.parser.abc_parser import AbstractParser


# fmt: off
resource_monitor_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "credit_quota": {
                "type": "integer"
            },
            "frequency": {
                "type": "string"
            },
            "triggers": {
                "type": "object",
                "additionalProperties": {
                    "type": "string"
                }
            }
        },
        "required": ["credit_quota", "frequency", "triggers"],
        "additionalProperties": False
    }
}
# fmt: on


class ResourceMonitorParser(AbstractParser):
    def load_blueprints(self):
        self.parse_multi_entity_file("resource_monitor", resource_monitor_json_schema, self.process_resource_monitor)

    def process_resource_monitor(self, resource_monitor_name, resource_monitor_params):
        bp = ResourceMonitorBlueprint(
            full_name=AccountObjectIdent(self.env_prefix, resource_monitor_name),
            credit_quota=int(resource_monitor_params.get("credit_quota")),
            frequency=str(resource_monitor_params.get("frequency")).upper(),
            triggers={int(k): str(v).upper() for k, v in resource_monitor_params.get("triggers").items()},
            comment=None,
        )

        self.config.add_blueprint(bp)
