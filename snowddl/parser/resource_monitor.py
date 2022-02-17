from snowddl.blueprint import ResourceMonitorBlueprint, Ident
from snowddl.parser.abc_parser import AbstractParser


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


class ResourceMonitorParser(AbstractParser):
    def load_blueprints(self):
        resource_monitor_config = self.parse_single_file(self.base_path / 'resource_monitor.yaml', resource_monitor_json_schema)

        for name, monitor in resource_monitor_config.items():
            bp = ResourceMonitorBlueprint(
                full_name=Ident(name),
                credit_quota=int(monitor.get('credit_quota')),
                frequency=str(monitor.get('frequency')).upper(),
                triggers={int(k): str(v).upper() for k, v in monitor.get('triggers').items()},
                comment=None,
            )

            self.config.add_blueprint(bp)
