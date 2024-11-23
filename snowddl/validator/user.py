from snowddl import UserBlueprint, BusinessRoleBlueprint
from snowddl.validator import AbstractValidator


class UserValidator(AbstractValidator):

    def validate(self):
        business_roles = self.config.get_blueprints_by_type(BusinessRoleBlueprint)

        for name, user in self.config.get_blueprints_by_type(UserBlueprint).items():
            for business_role in user.business_roles:
                if business_role not in business_roles:
                    raise ValueError(f"Business role {business_role} isn't defined")
