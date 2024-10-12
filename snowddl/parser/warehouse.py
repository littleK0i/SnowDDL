from snowddl.blueprint import WarehouseBlueprint, Ident, AccountObjectIdent
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


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
        self.parse_single_file(self.base_path / "warehouse.yaml", warehouse_json_schema, self.process_warehouse)

    def process_warehouse(self, f: ParsedFile):
        for warehouse_name, warehouse in f.params.items():
            warehouse_type = warehouse.get("type", "STANDARD").upper()

            resource_constraint = None
            resource_monitor = None

            if warehouse_type == "SNOWPARK-OPTIMIZED":
                resource_constraint = warehouse.get("resource_constraint", "MEMORY_16X")

            if warehouse.get("resource_monitor"):
                resource_monitor = AccountObjectIdent(self.env_prefix, warehouse["resource_monitor"])

            if warehouse.get("global_resource_monitor"):
                resource_monitor = Ident(warehouse["global_resource_monitor"])

            bp = WarehouseBlueprint(
                full_name=AccountObjectIdent(self.env_prefix, warehouse_name),
                type=warehouse_type,
                size=warehouse["size"],
                auto_suspend=warehouse.get("auto_suspend", 60),
                min_cluster_count=warehouse.get("min_cluster_count", 1),
                max_cluster_count=warehouse.get("max_cluster_count", 1),
                scaling_policy=warehouse.get("scaling_policy", "STANDARD").upper(),
                resource_monitor=resource_monitor,
                enable_query_acceleration=warehouse.get("enable_query_acceleration", False),
                query_acceleration_max_scale_factor=warehouse.get("query_acceleration_max_scale_factor", 8),
                warehouse_params=self.normalise_params_dict(warehouse.get("warehouse_params", {})),
                resource_constraint=resource_constraint,
                comment=warehouse.get("comment"),
            )

            self.config.add_blueprint(bp)
