from snowddl.blueprint import WarehouseBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType
from snowddl.resolver._utils import coalesce


class WarehouseResolver(AbstractResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.WAREHOUSE

    def get_existing_objects(self):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW WAREHOUSES LIKE {env_prefix:ls}", {
            'env_prefix': self.config.env_prefix,
        })

        for r in cur:
            if r['owner'] != self.engine.context.current_role:
                continue

            existing_objects[r['name']] = {
                "name": r['name'],
                "size": r['size'],
                "min_cluster_count": r.get('min_cluster_count', None),
                "max_cluster_count": r.get('max_cluster_count', None),
                "scaling_policy": r.get('scaling_policy', None),
                "auto_suspend": r['auto_suspend'],
                "resource_monitor": r['resource_monitor'] if r['resource_monitor'] != 'null' else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(WarehouseBlueprint)

    def create_object(self, bp: WarehouseBlueprint):
        query = self.engine.query_builder()

        query.append("CREATE WAREHOUSE {name:i}", {
            "name": bp.full_name,
        })

        query.append_nl(self._build_common_properties(bp))
        query.append_nl("AUTO_RESUME = TRUE")
        query.append_nl("INITIALLY_SUSPENDED = TRUE")

        self.engine.execute_safe_ddl(query)

        if bp.resource_monitor:
            self.engine.execute_safe_ddl("ALTER WAREHOUSE {full_name:i} SET RESOURCE_MONITOR = {resource_monitor:i}", {
                "full_name": bp.full_name,
                "resource_monitor": bp.resource_monitor,
            }, condition=self.engine.settings.execute_resource_monitor)

        return ResolveResult.CREATE

    def compare_object(self, bp: WarehouseBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if self._compare_properties(bp, row):
            result = ResolveResult.ALTER

        if self._compare_resource_monitor(bp, row):
            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl("DROP WAREHOUSE {name:i}", {
            "name": row['name'],
        })

        return ResolveResult.DROP

    def _compare_properties(self, bp: WarehouseBlueprint, row: dict):
        if self._normalise_warehouse_size(bp.size) == self._normalise_warehouse_size(row['size']) \
            and bp.auto_suspend == row['auto_suspend'] \
            and (row['min_cluster_count'] is None or coalesce(bp.min_cluster_count, 1) == row['min_cluster_count']) \
            and (row['max_cluster_count'] is None or coalesce(bp.max_cluster_count, 1) == row['max_cluster_count']) \
            and (row['scaling_policy'] is None or coalesce(bp.scaling_policy, 'STANDARD') == row['scaling_policy']):
            return False

        query = self.engine.query_builder()

        query.append("ALTER WAREHOUSE {full_name:i} SET", {
            "full_name": bp.full_name
        })

        query.append(self._build_common_properties(bp))

        self.engine.execute_safe_ddl(query)

        return True

    def _compare_resource_monitor(self, bp: WarehouseBlueprint, row: dict):
        if bp.resource_monitor is None and row['resource_monitor']:
            self.engine.execute_safe_ddl("ALTER WAREHOUSE {full_name:i} UNSET RESOURCE_MONITOR", {
                "full_name": bp.full_name,
            }, condition=self.engine.settings.execute_resource_monitor)

            return True

        if bp.resource_monitor and str(bp.resource_monitor) != row['resource_monitor']:
            self.engine.execute_safe_ddl("ALTER WAREHOUSE {full_name:i} SET RESOURCE_MONITOR = {resource_monitor:i}", {
                "full_name": bp.full_name,
                "resource_monitor": bp.resource_monitor,
            }, condition=self.engine.settings.execute_resource_monitor)

            return True

        return False

    def _build_common_properties(self, bp: WarehouseBlueprint):
        query = self.engine.query_builder()

        query.append_nl("WAREHOUSE_SIZE = {size}", {
            "size": self._normalise_warehouse_size(bp.size),
        })

        if bp.min_cluster_count:
            query.append_nl("MIN_CLUSTER_COUNT = {min_cluster_count:d}", {
                "min_cluster_count": bp.min_cluster_count,
            })

        if bp.max_cluster_count:
            query.append_nl("MAX_CLUSTER_COUNT = {max_cluster_count:d}", {
                "max_cluster_count": bp.max_cluster_count,
            })

        if bp.scaling_policy:
            query.append_nl("SCALING_POLICY = {scaling_policy}", {
                "scaling_policy": bp.scaling_policy,
            })

        query.append_nl("AUTO_SUSPEND = {auto_suspend:d}", {
            "auto_suspend": bp.auto_suspend,
        })

        return query

    def _normalise_warehouse_size(self, size: str):
        return size.upper().replace('-', '')

    def _post_process(self):
        if not self.engine.context.current_warehouse:
            return

        for result in self.resolved_objects.values():
            if result == ResolveResult.CREATE:
                # Revert current warehouse to original state if at least one object was created
                self.engine.execute_context_ddl("USE WAREHOUSE {full_name:i}", {
                    "full_name": self.engine.context.current_warehouse
                })

                break
