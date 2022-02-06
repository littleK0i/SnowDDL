from snowddl.blueprint import WarehouseBlueprint, Ident, IdentWithPrefix
from snowddl.parser.abc_parser import AbstractParser


warehouse_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
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
            "comment": {
                "type": "string"
            }
        },
        "required": ["size"],
        "additionalProperties": False
    }
}


class WarehouseParser(AbstractParser):
    def load_blueprints(self):
        warehouse_config = self.parse_single_file(self.base_path / 'warehouse.yaml', warehouse_json_schema)

        for warehouse_name, warehouse in warehouse_config.items():
            bp = WarehouseBlueprint(
                full_name=IdentWithPrefix(self.env_prefix, warehouse_name),
                size=warehouse['size'],
                auto_suspend=warehouse.get('auto_suspend', 60),
                min_cluster_count=warehouse.get('min_cluster_count'),
                max_cluster_count=warehouse.get('max_cluster_count'),
                scaling_policy=warehouse.get('scaling_policy'),
                resource_monitor=Ident(warehouse['resource_monitor']) if warehouse.get('resource_monitor') else None,
                comment=warehouse.get('comment'),
            )

            self.config.add_blueprint(bp)
