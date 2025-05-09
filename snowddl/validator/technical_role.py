from snowddl.blueprint import TechnicalRoleBlueprint
from snowddl.validator.abc_validator import AbstractValidator


class TechnicalRoleValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(TechnicalRoleBlueprint)

    def validate_blueprint(self, bp: TechnicalRoleBlueprint):
        self._validate_grant_patterns(bp)
        self._validate_future_grant_patterns(bp)

    def _validate_grant_patterns(self, bp: TechnicalRoleBlueprint):
        for grant_pattern in bp.grant_patterns:
            if not self.config.get_blueprints_by_type_and_pattern(grant_pattern.on.blueprint_cls, grant_pattern.pattern):
                raise ValueError(
                    f"Technical role [{bp.full_name}] grant pattern [{grant_pattern.pattern}] "
                    f"does not match any objects of type [{grant_pattern.on.name}]"
                )

            if grant_pattern.privilege == "ALL":
                raise ValueError(
                    f"Technical role [{bp.full_name}] with grant privilege [{grant_pattern.on.name}:ALL] is not supported, "
                    f"each individual privilege must be defined explicitly, e.g. [TABLE:SELECT,UPDATE,DELETE]"
                )

            if grant_pattern.privilege == "OWNERSHIP":
                raise ValueError(
                    f"Technical role [{bp.full_name}] with grant privilege [{grant_pattern.on.name}:OWNERSHIP] is not supported, "
                    f"ownership belongs to database_owner, schema_owner or snowddl admin role"
                )

    def _validate_future_grant_patterns(self, bp: TechnicalRoleBlueprint):
        for future_grant_pattern in bp.future_grant_patterns:
            if not self.config.get_blueprints_by_type_and_pattern(
                future_grant_pattern.in_parent.blueprint_cls, future_grant_pattern.pattern
            ):
                raise ValueError(
                    f"Technical role [{bp.full_name}] future grant pattern [{future_grant_pattern.pattern}] "
                    f"does not match any objects of type [{future_grant_pattern.in_parent.name}]"
                )

            if future_grant_pattern.privilege == "ALL":
                raise ValueError(
                    f"Technical role [{bp.full_name}] with future grant privilege [{future_grant_pattern.on_future.name}:ALL] is not supported, "
                    f"each individual privilege must be defined explicitly, e.g. [TABLE:SELECT,UPDATE,DELETE]"
                )

            if future_grant_pattern.privilege == "OWNERSHIP":
                raise ValueError(
                    f"Technical role [{bp.full_name}] with future grant privilege [{future_grant_pattern.on_future.name}:OWNERSHIP] is not supported, "
                    f"ownership belongs to database_owner, schema_owner or snowddl admin role"
                )
