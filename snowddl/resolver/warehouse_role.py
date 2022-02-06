from snowddl.blueprint import RoleBlueprint, WarehouseBlueprint, Grant
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver, ObjectType


class WarehouseRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.WAREHOUSE_ROLE_SUFFIX

    def get_blueprints(self):
        blueprints = []

        for warehouse in self.config.get_blueprints_by_type(WarehouseBlueprint).values():
            blueprints.append(self.get_blueprint_usage_role(warehouse))
            blueprints.append(self.get_blueprint_monitor_role(warehouse))

        return {str(bp.full_name): bp for bp in blueprints}

    def get_blueprint_usage_role(self, warehouse: WarehouseBlueprint):
        grants = []

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.WAREHOUSE,
            name=warehouse.full_name,
        ))

        grants.append(Grant(
            privilege="OPERATE",
            on=ObjectType.WAREHOUSE,
            name=warehouse.full_name,
        ))

        bp = RoleBlueprint(
            full_name=self.config.build_role_ident(warehouse.full_name, 'USAGE', self.get_role_suffix()),
            grants=grants,
            future_grants=[],
            comment=None,
        )

        return bp

    def get_blueprint_monitor_role(self, warehouse: WarehouseBlueprint):
        grants = []

        grants.append(Grant(
            privilege="MONITOR",
            on=ObjectType.WAREHOUSE,
            name=warehouse.full_name,
        ))

        grants.append(Grant(
            privilege="OPERATE",
            on=ObjectType.WAREHOUSE,
            name=warehouse.full_name,
        ))

        bp = RoleBlueprint(
            full_name=self.config.build_role_ident(warehouse.full_name, 'MONITOR', self.get_role_suffix()),
            grants=grants,
            future_grants=[],
            comment=None,
        )

        return bp
