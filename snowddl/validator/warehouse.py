from snowddl.blueprint import WarehouseBlueprint
from snowddl.validator.abc_validator import AbstractValidator


class WarehouseValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(WarehouseBlueprint)

    def validate_blueprint(self, bp: WarehouseBlueprint):
        self._validate_resource_constraint(bp)
        self._validate_size(bp)
        self._validate_adaptive_params(bp)

    def _validate_resource_constraint(self, bp: WarehouseBlueprint):
        if bp.type == "SNOWPARK-OPTIMIZED" and bp.resource_constraint is None:
            raise ValueError(f"Resource constraint must be defined for SNOWPARK-OPTIMIZED warehouse [{bp.full_name}]")

        if bp.resource_constraint in ("STANDARD_GEN_1", "STANDARD_GEN_2"):
            raise ValueError(f"It is no longer possible to set WAREHOUSE generation using [resource_constraint] parameter "
                             f"Please use [generation] parameter instead for WAREHOUSE [{bp.full_name}]")

    def _validate_size(self, bp: WarehouseBlueprint):
        # WAREHOUSE_SIZE is not a valid property for ADAPTIVE warehouses, so size is
        # optional for that type only; every other type still requires it.
        if bp.type != "ADAPTIVE" and bp.size is None:
            raise ValueError(f"Missing required parameter [size] for warehouse [{bp.full_name}]")

    def _validate_adaptive_params(self, bp: WarehouseBlueprint):
        # MAX_QUERY_PERFORMANCE_LEVEL and QUERY_THROUGHPUT_MULTIPLIER are core properties
        # of the ADAPTIVE warehouse type, they cannot be set for any other type.
        if bp.type != "ADAPTIVE" and bp.max_query_performance_level is not None:
            raise ValueError(
                f"Parameter [max_query_performance_level] is only valid for ADAPTIVE warehouse [{bp.full_name}], "
                f"but warehouse type is [{bp.type}]"
            )

        if bp.type != "ADAPTIVE" and bp.query_throughput_multiplier is not None:
            raise ValueError(
                f"Parameter [query_throughput_multiplier] is only valid for ADAPTIVE warehouse [{bp.full_name}], "
                f"but warehouse type is [{bp.type}]"
            )
