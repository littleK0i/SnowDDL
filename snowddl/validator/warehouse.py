from snowddl.blueprint import WarehouseBlueprint
from snowddl.validator.abc_validator import AbstractValidator


class WarehouseValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(WarehouseBlueprint)

    def validate_blueprint(self, bp: WarehouseBlueprint):
        if bp.type == "STANDARD":
            self._validate_standard_wh(bp)
        elif bp.type == "SNOWPARK-OPTIMIZED":
            self.validate_snowpark_optimized_wh(bp)
        elif bp.type == "ADAPTIVE":
            self._validate_adaptive_wh(bp)
        else:
            raise ValueError(f"Unexpected type [{bp.type}] for warehouse [{bp.full_name}]")

    def validate_snowpark_optimized_wh(self, bp: WarehouseBlueprint):
        if bp.size is None:
            raise ValueError(
                f"Missing required parameter [size] for SNOWPARK-OPTIMIZED warehouse [{bp.full_name}]"
            )

        if bp.resource_constraint is None:
            raise ValueError(
                f"Missing required parameter [resource_constraint] for SNOWPARK-OPTIMIZED warehouse [{bp.full_name}]"
            )

        if bp.max_query_performance_level is not None:
            raise ValueError(
                f"Parameter [max_query_performance_level] is only valid for ADAPTIVE warehouse [{bp.full_name}], "
                f"but warehouse type is [{bp.type}]"
            )

        if bp.query_throughput_multiplier is not None:
            raise ValueError(
                f"Parameter [query_throughput_multiplier] is only valid for ADAPTIVE warehouse [{bp.full_name}], "
                f"but warehouse type is [{bp.type}]"
            )

    def _validate_adaptive_wh(self, bp: WarehouseBlueprint):
        if bp.max_query_performance_level is None:
            raise ValueError(
                f"Missing required parameter [max_query_performance_level] for ADAPTIVE warehouse [{bp.full_name}]"
            )

        if bp.query_throughput_multiplier is None:
            raise ValueError(
                f"Missing required parameter [query_throughput_multiplier] for ADAPTIVE warehouse [{bp.full_name}]"
            )

    def _validate_standard_wh(self, bp: WarehouseBlueprint):
        if bp.size is None:
            raise ValueError(f"Missing required parameter [size] for STANDARD warehouse [{bp.full_name}]")

        if bp.resource_constraint in ("STANDARD_GEN_1", "STANDARD_GEN_2"):
            raise ValueError(f"It is no longer possible to set WAREHOUSE generation using [resource_constraint] parameter "
                             f"Please use [generation] parameter instead for STANDARD warehouse [{bp.full_name}]")

        if bp.max_query_performance_level is not None:
            raise ValueError(
                f"Parameter [max_query_performance_level] is only valid for ADAPTIVE warehouse [{bp.full_name}], "
                f"but warehouse type is [{bp.type}]"
            )

        if bp.query_throughput_multiplier is not None:
            raise ValueError(
                f"Parameter [query_throughput_multiplier] is only valid for ADAPTIVE warehouse [{bp.full_name}], "
                f"but warehouse type is [{bp.type}]"
            )
