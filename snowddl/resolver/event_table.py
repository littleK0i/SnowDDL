from snowddl.blueprint import EventTableBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class EventTableResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.EVENT_TABLE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW EVENT TABLES IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            full_name = f"{r['database_name']}.{r['schema_name']}.{r['name']}"
            existing_objects[full_name] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "owner": r["owner"],
                "retention_time": int(r["retention_time"]),
                "cluster_by": r["cluster_by"] if r["cluster_by"] else None,
                "change_tracking": bool(r["change_tracking"] == "ON"),
                "search_optimization": bool(r.get("search_optimization") == "ON"),
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(EventTableBlueprint)

    def create_object(self, bp: EventTableBlueprint):
        query = self._build_create_table(bp)
        self.engine.execute_safe_ddl(query)

        return ResolveResult.CREATE

    def compare_object(self, bp: EventTableBlueprint, row: dict):
        safe_alters = []
        unsafe_alters = []

        # Change tracking
        if bp.change_tracking != row["change_tracking"]:
            unsafe_alters.append(
                self.engine.format(
                    "SET CHANGE_TRACKING = {change_tracking:b}",
                    {
                        "change_tracking": bp.change_tracking,
                    },
                )
            )

        # Comment
        if bp.comment != row["comment"]:
            if bp.comment:
                safe_alters.append(
                    self.engine.format(
                        "SET COMMENT = {comment}",
                        {
                            "comment": bp.comment,
                        },
                    )
                )
            else:
                safe_alters.append(self.engine.format("UNSET COMMENT"))

        # Apply changes
        result = ResolveResult.NOCHANGE

        if safe_alters or unsafe_alters:
            for alter in safe_alters:
                self.engine.execute_safe_ddl(
                    "ALTER TABLE {full_name:i} {alter:r}",
                    {
                        "full_name": bp.full_name,
                        "alter": alter,
                    },
                )

            for alter in unsafe_alters:
                self.engine.execute_unsafe_ddl(
                    "ALTER TABLE {full_name:i} {alter:r}",
                    {
                        "full_name": bp.full_name,
                        "alter": alter,
                    },
                )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP TABLE {database:i}.{schema:i}.{table_name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "table_name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_create_table(self, bp: EventTableBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE EVENT TABLE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        if bp.change_tracking:
            query.append_nl("CHANGE_TRACKING = TRUE")

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        return query
