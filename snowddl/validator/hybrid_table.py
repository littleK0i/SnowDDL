from snowddl.blueprint import HybridTableBlueprint
from snowddl.validator.abc_validator import AbstractValidator


class HybridTableValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(HybridTableBlueprint)

    def validate_blueprint(self, bp: HybridTableBlueprint):
        self._validate_depends_on(bp)

    def _validate_depends_on(self, bp: HybridTableBlueprint):
        for depends_on_name in bp.depends_on:
            if depends_on_name == bp.full_name:
                raise ValueError(f"Hybrid table [{bp.full_name}] cannot depend on itself")

            if depends_on_name not in self.config.get_blueprints_by_type(HybridTableBlueprint):
                raise ValueError(
                    f"Hybrid table [{bp.full_name}] depends on another hybrid table "
                    f"[{depends_on_name}] which does not exist in config"
                )
