from snowddl.blueprint import AlertBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class AlertResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.ALERT

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW ALERTS IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "owner": r["owner"],
                "warehouse": r["warehouse"],
                "schedule": r["schedule"],
                "state": r["state"],
                "condition": r["condition"],
                "action": r["action"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(AlertBlueprint)

    def create_object(self, bp: AlertBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE ALERT {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        if bp.warehouse:
            query.append_nl(
                "WAREHOUSE = {warehouse:i}",
                {
                    "warehouse": bp.warehouse,
                },
            )

        query.append_nl(
            "SCHEDULE = {schedule}",
            {
                "schedule": bp.schedule,
            },
        )

        query.append_nl("IF(EXISTS(")
        query.append_nl(bp.condition)
        query.append_nl("))")

        query.append_nl("THEN")
        query.append_nl(bp.action)

        self.engine.execute_safe_ddl(query)

        return ResolveResult.CREATE

    def compare_object(self, bp: AlertBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if bp.warehouse != row["warehouse"]:
            if bp.warehouse:
                self.engine.execute_safe_ddl(
                    "ALTER ALERT {full_name:i} SET WAREHOUSE = {warehouse:i}",
                    {
                        "full_name": bp.full_name,
                        "warehouse": bp.warehouse,
                    },
                )
            else:
                self.engine.execute_safe_ddl(
                    "ALTER ALERT {full_name:i} UNSET WAREHOUSE",
                    {
                        "full_name": bp.full_name,
                        "warehouse": bp.warehouse,
                    },
                )

            result = ResolveResult.ALTER

        if str(bp.schedule) != row["schedule"]:
            self.engine.execute_safe_ddl(
                "ALTER ALERT {full_name:i} SET SCHEDULE = {schedule}",
                {
                    "full_name": bp.full_name,
                    "schedule": bp.schedule,
                },
            )

            result = ResolveResult.ALTER

        if str(bp.condition) != row["condition"]:
            query = self.engine.query_builder()

            query.append(
                "ALTER ALERT {full_name:i} MODIFY CONDITION EXISTS (",
                {
                    "full_name": bp.full_name,
                },
            )

            query.append_nl(bp.condition)
            query.append_nl(")")

            self.engine.execute_safe_ddl(query)

            result = ResolveResult.ALTER

        if str(bp.action) != row["action"]:
            query = self.engine.query_builder()

            query.append(
                "ALTER ALERT {full_name:i} MODIFY ACTION",
                {
                    "full_name": bp.full_name,
                },
            )

            query.append_nl(bp.action)

            self.engine.execute_safe_ddl(query)

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl(
            "DROP ALERT {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP
