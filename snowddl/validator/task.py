from snowddl.blueprint import TaskBlueprint
from snowddl.validator.abc_validator import AbstractValidator


class TaskValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(TaskBlueprint)

    def validate_blueprint(self, bp: TaskBlueprint):
        self._validate_depends_on(bp)

    def _validate_depends_on(self, bp: TaskBlueprint):
        for depends_on_name in bp.depends_on:
            if depends_on_name == bp.full_name:
                raise ValueError(f"Task [{bp.full_name}] cannot depend on itself")

            if depends_on_name not in self.config.get_blueprints_by_type(TaskBlueprint):
                raise ValueError(
                    f"Task [{bp.full_name}] depends on another task " f"[{depends_on_name}] which does not exist in config"
                )
