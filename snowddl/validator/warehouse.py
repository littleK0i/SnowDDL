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

        if bp.resource_constraint in ("STANDARD_GEN_1", "STANDARD_GEN_2"):
            raise ValueError(f"It is no longer possible to set WAREHOUSE generation using [resource_constraint] parameter "
                             f"Please use [generation] parameter instead for WAREHOUSE [{bp.full_name}]")
