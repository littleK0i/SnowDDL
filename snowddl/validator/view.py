from snowddl.blueprint import ViewBlueprint
from snowddl.validator.abc_validator import AbstractValidator


class ViewValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(ViewBlueprint)

    def validate_blueprint(self, bp: ViewBlueprint):
        self._validate_depends_on(bp)

    def _validate_depends_on(self, bp: ViewBlueprint):
        for depends_on_name in bp.depends_on:
            if depends_on_name == bp.full_name:
                raise ValueError(f"View [{bp.full_name}] cannot depend on itself")

            if depends_on_name not in self.config.get_blueprints_by_type(ViewBlueprint):
                raise ValueError(
                    f"View [{bp.full_name}] depends on another view " f"[{depends_on_name}] which does not exist in config"
                )
