from snowddl.blueprint import DynamicTableBlueprint
from snowddl.validator.abc_validator import AbstractValidator


class DynamicTableValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(DynamicTableBlueprint)

    def validate_blueprint(self, bp: DynamicTableBlueprint):
        self._validate_depends_on(bp)

    def _validate_depends_on(self, bp: DynamicTableBlueprint):
        for depends_on_name in bp.depends_on:
            if depends_on_name == bp.full_name:
                raise ValueError(f"Dynamic table [{bp.full_name}] cannot depend on itself")

            if depends_on_name not in self.config.get_blueprints_by_type(DynamicTableBlueprint):
                raise ValueError(f"Dynamic table [{bp.full_name}] depends on another dynamic table "
                                 f"[{depends_on_name}] which does not exist in config")
