from snowddl.blueprint import WarehouseBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType, Edition
from snowddl.resolver._utils import compare_dynamic_param_value


class WarehouseResolver(AbstractResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.WAREHOUSE

    def get_existing_objects(self):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW WAREHOUSES LIKE {env_prefix:ls}",
            {
                "env_prefix": self.config.env_prefix,
            },
        )

        for r in cur:
            if r["owner"] != self.engine.context.current_role:
                continue

            existing_objects[r["name"]] = {
                "name": r["name"],
                "state": r["state"],
                "type": r["type"],
                "size": r["size"],
                "min_cluster_count": r.get("min_cluster_count", None),
                "max_cluster_count": r.get("max_cluster_count", None),
                "scaling_policy": r.get("scaling_policy", None),
                "auto_suspend": r["auto_suspend"],
                "resource_monitor": r["resource_monitor"] if r["resource_monitor"] != "null" else None,
                "enable_query_acceleration": r.get("enable_query_acceleration") == "true",
                "query_acceleration_max_scale_factor": r.get("query_acceleration_max_scale_factor"),
                "resource_constraint": r.get("resource_constraint"),
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(WarehouseBlueprint)

    def create_object(self, bp: WarehouseBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE WAREHOUSE {name:i}",
            {
                "name": bp.full_name,
            },
        )

        query.append_nl("WAREHOUSE_TYPE = {type}", {"type": bp.type})
        query.append_nl("WAREHOUSE_SIZE = {size}", {"size": self._normalise_warehouse_size(bp.size)})
        query.append_nl("AUTO_SUSPEND = {auto_suspend:d}", {"auto_suspend": bp.auto_suspend})
        query.append_nl("AUTO_RESUME = TRUE")
        query.append_nl("INITIALLY_SUSPENDED = TRUE")

        if bp.resource_constraint:
            query.append_nl("RESOURCE_CONSTRAINT = {resource_constraint}", {"resource_constraint": bp.resource_constraint})

        if self.engine.context.edition >= Edition.ENTERPRISE:
            query.append_nl("MIN_CLUSTER_COUNT = {min_cluster_count:d}", {"min_cluster_count": bp.min_cluster_count})
            query.append_nl("MAX_CLUSTER_COUNT = {max_cluster_count:d}", {"max_cluster_count": bp.max_cluster_count})
            query.append_nl("SCALING_POLICY = {scaling_policy}", {"scaling_policy": bp.scaling_policy})

            if bp.enable_query_acceleration:
                query.append_nl(
                    "ENABLE_QUERY_ACCELERATION = {enable_query_acceleration:b}",
                    {"enable_query_acceleration": bp.enable_query_acceleration},
                )

            if bp.query_acceleration_max_scale_factor:
                query.append_nl(
                    "QUERY_ACCELERATION_MAX_SCALE_FACTOR = {query_acceleration_max_scale_factor:d}",
                    {"query_acceleration_max_scale_factor": bp.query_acceleration_max_scale_factor},
                )

        query.append_nl("COMMENT = {comment}", {"comment": bp.comment})
        query.append_nl(self._build_common_parameters(bp))

        self.engine.execute_safe_ddl(query)

        if bp.resource_monitor:
            self.engine.execute_safe_ddl(
                "ALTER WAREHOUSE {full_name:i} SET RESOURCE_MONITOR = {resource_monitor:i}",
                {
                    "full_name": bp.full_name,
                    "resource_monitor": bp.resource_monitor,
                },
                condition=self.engine.settings.execute_resource_monitor,
            )

        return ResolveResult.CREATE

    def compare_object(self, bp: WarehouseBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if self._compare_properties(bp, row):
            result = ResolveResult.ALTER

        if self._compare_resource_monitor(bp, row):
            result = ResolveResult.ALTER

        if self._compare_parameters(bp):
            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP WAREHOUSE {name:i}",
            {
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _compare_properties(self, bp: WarehouseBlueprint, row: dict):
        query = self.engine.query_builder()

        query.append(
            "ALTER WAREHOUSE {name:i} SET",
            {
                "name": bp.full_name,
            },
        )

        if bp.type != row["type"]:
            query.append_nl("WAREHOUSE_TYPE = {type}", {"type": bp.type})

        if self._normalise_warehouse_size(bp.size) != self._normalise_warehouse_size(row["size"]):
            query.append_nl("WAREHOUSE_SIZE = {size}", {"size": self._normalise_warehouse_size(bp.size)})

        if bp.auto_suspend != row["auto_suspend"]:
            query.append_nl("AUTO_SUSPEND = {auto_suspend:d}", {"auto_suspend": bp.auto_suspend})

        if bp.resource_constraint != row["resource_constraint"]:
            query.append_nl("RESOURCE_CONSTRAINT = {resource_constraint}", {"resource_constraint": bp.resource_constraint})

        if self.engine.context.edition >= Edition.ENTERPRISE:
            if bp.min_cluster_count != row["min_cluster_count"]:
                query.append_nl("MIN_CLUSTER_COUNT = {min_cluster_count:d}", {"min_cluster_count": bp.min_cluster_count})

            if bp.max_cluster_count != row["max_cluster_count"]:
                query.append_nl("MAX_CLUSTER_COUNT = {max_cluster_count:d}", {"max_cluster_count": bp.max_cluster_count})

            if bp.scaling_policy != row["scaling_policy"]:
                query.append_nl("SCALING_POLICY = {scaling_policy}", {"scaling_policy": bp.scaling_policy})

            if bp.enable_query_acceleration != row["enable_query_acceleration"]:
                query.append_nl(
                    "ENABLE_QUERY_ACCELERATION = {enable_query_acceleration:b}",
                    {"enable_query_acceleration": bp.enable_query_acceleration},
                )

            if bp.query_acceleration_max_scale_factor != row["query_acceleration_max_scale_factor"]:
                query.append_nl(
                    "QUERY_ACCELERATION_MAX_SCALE_FACTOR = {query_acceleration_max_scale_factor:d}",
                    {"query_acceleration_max_scale_factor": bp.query_acceleration_max_scale_factor},
                )

        if bp.comment != row["comment"]:
            query.append_nl("COMMENT = {comment}", {"comment": bp.comment})

        if query.fragment_count() > 1:
            self.engine.execute_safe_ddl(query)
            return True

        return False

    def _compare_parameters(self, bp: WarehouseBlueprint):
        existing_params = self._get_existing_warehouse_parameters(bp)
        query = self.engine.query_builder()

        query.append(
            "ALTER WAREHOUSE {name:i} SET",
            {
                "name": bp.full_name,
            },
        )

        for param_name, param_value in bp.warehouse_params.items():
            if param_name not in existing_params:
                raise ValueError(f"Unknown parameter [{param_name}] for warehouse [{bp.full_name}]")

            if compare_dynamic_param_value(param_value, existing_params[param_name]["value"]):
                continue

            # At least one parameter in blueprint does not match the existing value
            # Refresh all parameters for such warehouse
            query.append(self._build_common_parameters(bp))
            break

        # If parameter was set on WAREHOUSE level and does not exist in blueprint anymore
        # Unset such parameter and reset it to default
        for param_name, p in existing_params.items():
            if p["level"] == "WAREHOUSE" and p["key"] not in bp.warehouse_params:
                # Setting parameter to NULL equals to UNSET
                query.append_nl(
                    "{param_name:r} = NULL",
                    {
                        "param_name": param_name,
                    },
                )

        if query.fragment_count() > 1:
            self.engine.execute_safe_ddl(query)
            return True

        return False

    def _compare_resource_monitor(self, bp: WarehouseBlueprint, row: dict):
        if bp.resource_monitor is None and row["resource_monitor"]:
            self.engine.execute_safe_ddl(
                "ALTER WAREHOUSE {full_name:i} UNSET RESOURCE_MONITOR",
                {
                    "full_name": bp.full_name,
                },
                condition=self.engine.settings.execute_resource_monitor,
            )

            return True

        if bp.resource_monitor and str(bp.resource_monitor) != row["resource_monitor"]:
            self.engine.execute_safe_ddl(
                "ALTER WAREHOUSE {full_name:i} SET RESOURCE_MONITOR = {resource_monitor:i}",
                {
                    "full_name": bp.full_name,
                    "resource_monitor": bp.resource_monitor,
                },
                condition=self.engine.settings.execute_resource_monitor,
            )

            return True

        return False

    def _build_common_parameters(self, bp: WarehouseBlueprint):
        query = self.engine.query_builder()

        for param_name, param_value in bp.warehouse_params.items():
            query.append_nl(
                "{param_name:r} = {param_value:dp}",
                {
                    "param_name": param_name,
                    "param_value": param_value,
                },
            )

        return query

    def _get_existing_warehouse_parameters(self, bp: WarehouseBlueprint):
        existing_params = {}

        cur = self.engine.execute_meta(
            "SHOW PARAMETERS IN WAREHOUSE {name:i}",
            {
                "name": bp.full_name,
            },
        )

        for r in cur:
            existing_params[r["key"]] = r

        return existing_params

    def _normalise_warehouse_size(self, size: str):
        return size.upper().replace("-", "")

    def _post_process(self):
        if not self.engine.context.current_warehouse:
            return

        for result in self.resolved_objects.values():
            if result == ResolveResult.CREATE:
                # Revert current warehouse to original state if at least one object was created
                self.engine.execute_context_ddl(
                    "USE WAREHOUSE {full_name:i}", {"full_name": self.engine.context.current_warehouse}
                )

                break
