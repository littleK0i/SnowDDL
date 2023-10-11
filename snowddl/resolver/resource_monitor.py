from snowddl.blueprint import ResourceMonitorBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class ResourceMonitorResolver(AbstractResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.RESOURCE_MONITOR

    def get_existing_objects(self):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW RESOURCE MONITORS LIKE {env_prefix:ls}",
            {
                "env_prefix": self.config.env_prefix,
            },
        )

        for r in cur:
            if r["owner"] != self.engine.context.current_role:
                continue

            triggers = {}

            triggers.update(self._parse_triggers(r["notify_at"], "NOTIFY"))
            triggers.update(self._parse_triggers(r["suspend_at"], "SUSPEND"))
            triggers.update(self._parse_triggers(r["suspend_immediately_at"], "SUSPEND_IMMEDIATE"))

            existing_objects[r["name"]] = {
                "name": r["name"],
                "credit_quota": int(float(r["credit_quota"])),
                "frequency": r["frequency"],
                "notify_at": r["notify_at"],
                "suspend_at": r["suspend_at"],
                "suspend_immediately_at": r["suspend_immediately_at"],
                "triggers": triggers,
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def _parse_triggers(self, val, action):
        triggers = {}

        if val is None:
            return triggers

        for threshold in val.split(","):
            threshold = threshold.strip(" %")
            triggers[int(threshold)] = action

        return triggers

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(ResourceMonitorBlueprint)

    def create_object(self, bp: ResourceMonitorBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE RESOURCE MONITOR {name:i}",
            {
                "name": bp.full_name,
            },
        )

        query.append_nl(
            "CREDIT_QUOTA = {credit_quota:d}",
            {
                "credit_quota": bp.credit_quota,
            },
        )

        query.append_nl(
            "FREQUENCY = {frequency}",
            {
                "frequency": bp.frequency,
            },
        )

        query.append_nl("START_TIMESTAMP = IMMEDIATELY")
        query.append_nl("TRIGGERS")

        for threshold, action in bp.triggers.items():
            query.append_nl(
                "ON {threshold:d} PERCENT DO {action:r}",
                {
                    "threshold": threshold,
                    "action": action,
                },
            )

        self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_resource_monitor)

        return ResolveResult.CREATE

    def compare_object(self, bp: ResourceMonitorBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if bp.credit_quota != row["credit_quota"]:
            self.engine.execute_unsafe_ddl(
                "ALTER RESOURCE MONITOR {name:i} SET CREDIT_QUOTA = {credit_quota:d}",
                {
                    "name": bp.full_name,
                    "credit_quota": bp.credit_quota,
                },
                condition=self.engine.settings.execute_resource_monitor,
            )

            result = ResolveResult.ALTER

        if bp.frequency != row["frequency"]:
            self.engine.execute_unsafe_ddl(
                "ALTER RESOURCE MONITOR {name:i} SET FREQUENCY = {frequency} START_TIMESTAMP = IMMEDIATELY",
                {
                    "name": bp.full_name,
                    "frequency": bp.frequency,
                },
                condition=self.engine.settings.execute_resource_monitor,
            )

            result = ResolveResult.ALTER

        if bp.triggers != row["triggers"]:
            query = self.engine.query_builder()

            query.append(
                "ALTER RESOURCE MONITOR {name:i}",
                {
                    "name": bp.full_name,
                },
            )

            query.append_nl("TRIGGERS")

            for threshold, action in bp.triggers.items():
                query.append_nl(
                    "ON {threshold:d} PERCENT DO {action:r}",
                    {
                        "threshold": threshold,
                        "action": action,
                    },
                )

            self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_resource_monitor)

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP RESOURCE MONITOR {name:i}",
            {
                "name": row["name"],
            },
            condition=self.engine.settings.execute_resource_monitor,
        )

        return ResolveResult.DROP
