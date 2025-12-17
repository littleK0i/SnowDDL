from snowddl.blueprint import BackupPolicyBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class BackupPolicyResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.BACKUP_POLICY

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW BACKUP POLICIES IN SCHEMA {database:i}.{schema:i}",
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
                "schedule": r["schedule"],
                "expire_after_days": r["expire_after_days"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(BackupPolicyBlueprint)

    def create_object(self, bp: BackupPolicyBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE BACKUP POLICY {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        if bp.schedule:
            query.append_nl(
                "SCHEDULE = {schedule}",
                {
                    "schedule": bp.schedule,
                },
            )

        if bp.expire_after_days:
            query.append_nl(
                "EXPIRE_AFTER_DAYS = {expire_after_days:d}",
                {
                    "expire_after_days": bp.expire_after_days,
                },
            )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        self.engine.execute_unsafe_ddl(query)

        return ResolveResult.CREATE

    def compare_object(self, bp: BackupPolicyBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if bp.schedule != row["schedule"]:
            if bp.schedule:
                self.engine.execute_unsafe_ddl(
                    "ALTER BACKUP POLICY {full_name:i} SET SCHEDULE = {schedule}",
                    {
                        "full_name": bp.full_name,
                        "schedule": bp.schedule,
                    },
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER BACKUP POLICY {full_name:i} UNSET SCHEDULE",
                    {
                        "full_name": bp.full_name,
                    },
                )

            result = ResolveResult.ALTER

        if bp.expire_after_days != row["expire_after_days"]:
            if bp.expire_after_days:
                self.engine.execute_unsafe_ddl(
                    "ALTER BACKUP POLICY {full_name:i} SET EXPIRE_AFTER_DAYS = {expire_after_days:d}",
                    {
                        "full_name": bp.full_name,
                        "expire_after_days": bp.expire_after_days,
                    },
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER BACKUP POLICY {full_name:i} UNSET EXPIRE_AFTER_DAYS",
                    {
                        "full_name": bp.full_name,
                    },
                )

            result = ResolveResult.ALTER

        if bp.comment != row["comment"]:
            self.engine.execute_unsafe_ddl(
                "ALTER BACKUP POLICY {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
            )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP BACKUP POLICY {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP
