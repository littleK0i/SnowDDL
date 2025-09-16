from snowddl.blueprint import SnapshotSetBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class SnapshotSetResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.SNAPSHOT_SET

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW SNAPSHOT SETS IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            object_type = r["object_kind"]  # more fancy logic is going to be added here

            if object_type == "DATABASE":
                object_name = r["object_name"]
            elif object_type == "SCHEMA":
                object_name = f"{r['object_database_name']}.{r['object_name']}"
            else:
                object_name = f"{r['object_database_name']}.{r['object_schema_name']}.{r['object_name']}"

            if r["snapshot_policy_name"]:
                snapshot_policy = f"{r['snapshot_policy_database_name']}.{r['snapshot_policy_schema_name']}.{r['snapshot_policy_name']}"
            else:
                snapshot_policy = None

            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "owner": r["owner_role"],
                "object_type": object_type,
                "object_name": object_name,
                "snapshot_policy": snapshot_policy,
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(SnapshotSetBlueprint)

    def create_object(self, bp: SnapshotSetBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE SNAPSHOT SET {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        query.append_nl(
            "FOR {object_type:r} {object_name:i}",
            {
                "object_type": bp.object_type.singular,
                "object_name": bp.object_name,
            },
        )

        if bp.snapshot_policy:
            query.append_nl(
                "WITH SNAPSHOT POLICY {snapshot_policy:i}",
                {
                    "snapshot_policy": bp.snapshot_policy,
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

    def compare_object(self, bp: SnapshotSetBlueprint, row: dict):
        result = ResolveResult.NOCHANGE
        replace_reasons = []

        if bp.snapshot_policy is None and row["snapshot_policy"] is not None:
            replace_reasons.append("Cannot remove snapshot policy from snapshot set")

        if bp.object_type.singular != row["object_type"]:
            replace_reasons.append("Object type for snapshot set was changed")

        if bp.object_name != row["object_name"]:
            replace_reasons.append("Object name for snapshot set was changed")

        if replace_reasons:
            query = self.engine.query_builder()

            query.append(
                "CREATE OR REPLACE SNAPSHOT SET {full_name:i}",
                {
                    "full_name": bp.full_name,
                },
            )

            query.append_nl(
                "FOR {object_type:r} {object_name:i}",
                {
                    "object_type": bp.object_type.singular,
                    "object_name": bp.object_name,
                },
            )

            if bp.snapshot_policy:
                query.append_nl(
                    "WITH SNAPSHOT POLICY {snapshot_policy:i}",
                    {
                        "snapshot_policy": bp.snapshot_policy,
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

            return ResolveResult.REPLACE

        if bp.snapshot_policy != row["snapshot_policy"]:
            if bp.snapshot_policy:
                self.engine.execute_unsafe_ddl(
                    "ALTER SNAPSHOT SET {full_name:i} APPLY SNAPSHOT POLICY {snapshot_policy:i} FORCE",
                    {
                        "full_name": bp.full_name,
                        "snapshot_policy": bp.snapshot_policy,
                    },
                )

                result = ResolveResult.ALTER

        if bp.comment != row["comment"]:
            self.engine.execute_unsafe_ddl(
                "ALTER SNAPSHOT SET {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
            )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP SNAPSHOT SET {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP
