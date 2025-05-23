from snowddl.blueprint import WarehouseBlueprint
from snowddl.validator.abc_validator import AbstractValidator


class WarehouseValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(WarehouseBlueprint)

    def validate_blueprint(self, bp: WarehouseBlueprint):
        self._validate_resource_constraint(bp)

    def _validate_resource_constraint(self, bp: WarehouseBlueprint):
        if bp.type == "SNOWPARK-OPTIMIZED" and bp.resource_constraint is None:
            raise ValueError(f"Resource constraint must be defined for SNOWPARK-OPTIMIZED warehouse [{bp.full_name}]")
