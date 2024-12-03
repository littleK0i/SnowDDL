from snowddl.blueprint import WarehouseBlueprint, Ident, AccountObjectIdent
from snowddl.parser.abc_parser import AbstractParser


# fmt: off
warehouse_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string"
            },
            "size": {
                "type": "string"
            },
            "min_cluster_count": {
                "type": "integer"
            },
            "max_cluster_count": {
                "type": "integer"
            },
            "scaling_policy": {
                "type": "string"
            },
            "auto_suspend": {
                "type": "integer"
            },
            "resource_monitor": {
                "type": "string"
            },
            "global_resource_monitor": {
                "type": "string"
            },
            "enable_query_acceleration": {
                "type": "boolean"
            },
            "query_acceleration_max_scale_factor": {
                "type": "integer"
            },
            "warehouse_params": {
                "type": "object",
                "additionalProperties": {
                    "type": ["boolean", "number", "string"]
                }
            },
            "resource_constraint": {
                "type": "string"
            },
            "comment": {
                "type": "string"
            }
        },
        "required": ["size"],
        "additionalProperties": False
    }
}
# fmt: on


class WarehouseParser(AbstractParser):
    def load_blueprints(self):
        self.parse_multi_entity_file("warehouse", warehouse_json_schema, self.process_warehouse)

    def process_warehouse(self, warehouse_name, warehouse_params):
        warehouse_type = warehouse_params.get("type", "STANDARD").upper()

        resource_constraint = None
        resource_monitor = None

        if warehouse_type == "SNOWPARK-OPTIMIZED":
            resource_constraint = warehouse_params.get("resource_constraint", "MEMORY_16X")

        if warehouse_params.get("resource_monitor"):
            resource_monitor = AccountObjectIdent(self.env_prefix, warehouse_params["resource_monitor"])

        if warehouse_params.get("global_resource_monitor"):
            resource_monitor = Ident(warehouse_params["global_resource_monitor"])

        bp = WarehouseBlueprint(
            full_name=AccountObjectIdent(self.env_prefix, warehouse_name),
            type=warehouse_type,
            size=warehouse_params["size"],
            auto_suspend=warehouse_params.get("auto_suspend", 60),
            min_cluster_count=warehouse_params.get("min_cluster_count", 1),
            max_cluster_count=warehouse_params.get("max_cluster_count", 1),
            scaling_policy=warehouse_params.get("scaling_policy", "STANDARD").upper(),
            resource_monitor=resource_monitor,
            enable_query_acceleration=warehouse_params.get("enable_query_acceleration", False),
            query_acceleration_max_scale_factor=warehouse_params.get("query_acceleration_max_scale_factor", 8),
            warehouse_params=self.normalise_params_dict(warehouse_params.get("warehouse_params", {})),
            resource_constraint=resource_constraint,
            comment=warehouse_params.get("comment"),
        )

        self.config.add_blueprint(bp)
