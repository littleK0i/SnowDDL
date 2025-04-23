from snowddl.blueprint import MaterializedViewBlueprint, Edition
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class MaterializedViewResolver(AbstractSchemaObjectResolver):
    skip_min_edition = Edition.ENTERPRISE

    def get_object_type(self) -> ObjectType:
        return ObjectType.MATERIALIZED_VIEW

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW MATERIALIZED VIEWS IN SCHEMA {database:i}.{schema:i}",
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
                "text": str(r["text"]).rstrip(";"),
                "is_secure": r["is_secure"] == "true",
                "cluster_by": r["cluster_by"] if r["cluster_by"] else None,
                "invalid": r["invalid"] == "true",
                "invalid_reason": r["invalid_reason"],
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(MaterializedViewBlueprint)

    def create_object(self, bp: MaterializedViewBlueprint):
        self.engine.execute_safe_ddl(self._build_create_materialized_view(bp))

        return ResolveResult.CREATE

    def compare_object(self, bp: MaterializedViewBlueprint, row: dict):
        query = self._build_create_materialized_view(bp)

        # If view text is exactly the same, and view is still valid, do nothing
        if row["text"] == str(query) and not row["invalid"]:
            return ResolveResult.NOCHANGE

        self.engine.execute_unsafe_ddl(query)

        return ResolveResult.REPLACE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP MATERIALIZED VIEW {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_create_materialized_view(self, bp: MaterializedViewBlueprint):
        query = self.engine.query_builder()

        query.append("CREATE OR REPLACE")

        if bp.is_secure:
            query.append("SECURE")

        query.append(
            "MATERIALIZED VIEW {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        query.append_nl("COPY GRANTS")

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

        if bp.cluster_by:
            query.append_nl(
                "CLUSTER BY ({cluster_by:r})",
                {
                    "cluster_by": bp.cluster_by,
                },
            )

        query.append_nl("AS")
        query.append_nl(bp.text)

        return query
