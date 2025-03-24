from snowddl.blueprint import RoleBlueprint, WarehouseBlueprint, Grant, build_role_ident
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver, ObjectType


class WarehouseUsageRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.WAREHOUSE_ACCESS_ROLE_SUFFIX

    def get_role_type(self):
        return self.config.USAGE_ROLE_TYPE

    def get_blueprints(self):
        blueprints = []

        for warehouse in self.config.get_blueprints_by_type(WarehouseBlueprint).values():
            blueprints.append(self.get_blueprint_usage_role(warehouse))

        return {str(bp.full_name): bp for bp in blueprints}

    def get_blueprint_usage_role(self, warehouse: WarehouseBlueprint):
        grants = []

        grants.append(
            Grant(
                privilege="USAGE",
                on=ObjectType.WAREHOUSE,
                name=warehouse.full_name,
            )
        )

        grants.append(
            Grant(
                privilege="OPERATE",
                on=ObjectType.WAREHOUSE,
                name=warehouse.full_name,
            )
        )

        bp = RoleBlueprint(
            full_name=build_role_ident(
                self.config.env_prefix, warehouse.full_name.name, self.config.USAGE_ROLE_TYPE, self.get_role_suffix()
            ),
            grants=grants,
            future_grants=[],
        )

        return bp
