from snowddl.blueprint import TechnicalRoleBlueprint
from snowddl.validator.abc_validator import AbstractValidator


class TechnicalRoleValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(TechnicalRoleBlueprint)

    def validate_blueprint(self, bp: TechnicalRoleBlueprint):
        self._validate_grant_patterns(bp)

    def _validate_grant_patterns(self, bp: TechnicalRoleBlueprint):
        for grant_pattern in bp.grant_patterns:
            if not self.config.get_blueprints_by_type_and_pattern(grant_pattern.on.blueprint_cls, grant_pattern.pattern):
                raise ValueError(
                    f"Technical role [{bp.full_name}] grant pattern [{grant_pattern.pattern}] "
                    f"does not match any objects of type [{grant_pattern.on.name}]"
                )
