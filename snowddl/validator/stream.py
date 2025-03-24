from snowddl.blueprint import EventTableBlueprint, StreamBlueprint, TableBlueprint, ViewBlueprint
from snowddl.validator.abc_validator import AbstractValidator


class StreamValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(StreamBlueprint)

    def validate_blueprint(self, bp: StreamBlueprint):
        self._validate_dependency(bp)

    def _validate_dependency(self, bp: StreamBlueprint):
        if bp.object_name not in self.config.get_blueprints_by_type(bp.object_type.blueprint_cls):
            raise ValueError(
                f"Stream [{bp.full_name}] depends on {bp.object_type.name} " f"[{bp.object_name}] which does not exist in config"
            )

        target_bp = self.config.get_blueprints_by_type(bp.object_type.blueprint_cls)[str(bp.object_name)]

        if isinstance(target_bp, (EventTableBlueprint, TableBlueprint, ViewBlueprint)):
            if not target_bp.change_tracking:
                raise ValueError(
                    f"Stream [{bp.full_name}] depends on {bp.object_type.name} "
                    f"[{bp.object_name}], but change_tracking is not enabled on it"
                )
