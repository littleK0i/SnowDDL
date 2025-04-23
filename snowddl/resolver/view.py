from snowddl.blueprint import ViewBlueprint

from snowddl.error import SnowDDLExecuteError
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class ViewResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.VIEW

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW VIEWS IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            if r["is_materialized"] == "true":
                continue

            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "owner": r["owner"],
                "text": str(r["text"]).rstrip(";"),
                "is_secure": r["is_secure"] == "true",
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(ViewBlueprint)

    def create_object(self, bp: ViewBlueprint):
        self.engine.execute_safe_ddl(self._build_create_view(bp))

        # Comments on views are broken and must be applied separately
        if bp.comment:
            self.engine.execute_safe_ddl(
                "COMMENT ON VIEW {full_name:i} IS {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
            )

        return ResolveResult.CREATE

    def compare_object(self, bp: ViewBlueprint, row: dict):
        query = self._build_create_view(bp)

        # If view text is exactly the same
        if row["text"] == str(query):
            try:
                # ... and it is possible to query view (underlying objects were not changed)
                self.engine.describe_meta(
                    "SELECT * FROM {full_name:i}",
                    {
                        "full_name": bp.full_name,
                    },
                )
            except SnowDDLExecuteError as e:
                self.engine.logger.debug(
                    f"View [{bp.full_name}] caused describe error [{e.snow_exc.errno}]: {e.snow_exc.raw_msg}"
                )
            else:
                # Comments on views are broken and must be applied separately
                if bp.comment != row["comment"]:
                    self.engine.execute_safe_ddl(
                        "COMMENT ON VIEW {full_name:i} IS {comment}",
                        {
                            "full_name": bp.full_name,
                            "comment": bp.comment if bp.comment else "",
                        },
                    )

                    return ResolveResult.ALTER
                else:
                    return ResolveResult.NOCHANGE
        else:
            self.engine.logger.debug(f"View [{bp.full_name}] text did not match")

        # Replace view if we got here
        self.engine.execute_safe_ddl(query)

        # Comments on views are broken and must be applied separately
        if bp.comment:
            self.engine.execute_safe_ddl(
                "COMMENT ON VIEW {full_name:i} IS {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
            )

        return ResolveResult.REPLACE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl(
            "DROP VIEW {database:i}.{schema:i}.{view_name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "view_name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_create_view(self, bp: ViewBlueprint):
        query = self.engine.query_builder()

        query.append("CREATE OR REPLACE")

        if bp.is_secure:
            query.append("SECURE")

        query.append(
            "VIEW {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        if bp.columns:
            query.append_nl("(")

            for idx, c in enumerate(bp.columns):
                query.append_nl(
                    "    {comma:r}{col_name:i}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "col_name": c.name,
                    },
                )

                if c.comment:
                    query.append(
                        "COMMENT {col_comment}",
                        {
                            "col_comment": c.comment,
                        },
                    )

            query.append_nl(")")

        if bp.change_tracking:
            query.append_nl("CHANGE_TRACKING = TRUE")

        query.append_nl("COPY GRANTS")
        query.append_nl("AS")
        query.append_nl(bp.text)

        return query
