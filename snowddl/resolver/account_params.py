from snowddl.blueprint import AccountParameterBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType
from snowddl.resolver._utils import compare_dynamic_param_value


class AccountParameterResolver(AbstractResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.ACCOUNT_PARAMETER

    def get_existing_objects(self):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW PARAMETERS FOR ACCOUNT")

        for r in cur:
            existing_objects[r["key"]] = {
                "key": r["key"],
                "value": r["value"],
                "default": r["default"],
                "level": r["level"],
                "type": r["type"],
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(AccountParameterBlueprint)

    def create_object(self, bp: AccountParameterBlueprint):
        raise ValueError(f"Unknown account parameter [{bp.full_name}]")

    def compare_object(self, bp: AccountParameterBlueprint, row: dict):
        if compare_dynamic_param_value(bp.value, row["value"]):
            return ResolveResult.NOCHANGE

        self.engine.execute_unsafe_ddl(
            "ALTER ACCOUNT SET {param_name:r} = {param_value:dp}",
            {
                "param_name": row["key"],
                "param_value": bp.value,
            },
            condition=self.engine.settings.execute_account_params,
        )

        return ResolveResult.ALTER

    def drop_object(self, row: dict):
        if row["value"] != row["default"] and row["level"] == "ACCOUNT":
            self.engine.execute_unsafe_ddl(
                "ALTER ACCOUNT UNSET {param_name:r}",
                {
                    "param_name": row["key"],
                },
                condition=self.engine.settings.execute_account_params,
            )

            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def destroy(self):
        pass
