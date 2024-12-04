from snowddl.blueprint import BusinessRoleBlueprint, UserBlueprint, WarehouseBlueprint
from snowddl.validator.abc_validator import AbstractValidator


class UserValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(UserBlueprint)

    def validate_blueprint(self, bp: UserBlueprint):
        self._validate_business_roles(bp)
        self._validate_default_warehouse(bp)
        self._validate_user_type_properties(bp)

    def _validate_business_roles(self, bp: UserBlueprint):
        for business_role in bp.business_roles:
            if business_role not in self.config.get_blueprints_by_type(BusinessRoleBlueprint):
                raise ValueError(f"User [{bp.full_name}] references to undefined business role [{business_role}]")

    def _validate_default_warehouse(self, bp: UserBlueprint):
        if bp.default_warehouse and bp.default_warehouse not in self.config.get_blueprints_by_type(WarehouseBlueprint):
            raise ValueError(f"User [{bp.full_name}] references to undefined default warehouse [{bp.default_warehouse}]")

    def _validate_user_type_properties(self, bp: UserBlueprint):
        if bp.type in ("SERVICE", "LEGACY_SERVICE"):
            if bp.first_name:
                raise ValueError(f"Property [first_name] is not allowed for user [{bp.full_name}] with type [{bp.type}]")

            if bp.last_name:
                raise ValueError(f"Property [last_name] is not allowed for user [{bp.full_name}] with type [{bp.type}]")

        if bp.type == "SERVICE":
            if bp.password:
                raise ValueError(f"Property [password] is not allowed for user [{bp.full_name}] with type [{bp.type}]")
