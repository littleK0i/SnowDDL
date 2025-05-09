from snowddl.blueprint import SemanticViewBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class SemanticViewResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.SEMANTIC_VIEW

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW SEMANTIC VIEWS IN SCHEMA {database:i}.{schema:i}",
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
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(SemanticViewBlueprint)

    def create_object(self, bp: SemanticViewBlueprint):
        create_query = self._build_create_semantic_view_sql(bp)

        # Temporary workaround due to not being able to change comment on existing SEMANTIC VIEW
        create_query.append_nl(
            "COMMENT = {comment}",
            {
                "comment": create_query.add_short_hash(bp.comment),
            },
        )

        self.engine.execute_safe_ddl(create_query)

        return ResolveResult.CREATE

    def compare_object(self, bp: SemanticViewBlueprint, row: dict):
        create_query = self._build_create_semantic_view_sql(bp)

        if not create_query.compare_short_hash(row["comment"]):
            # Temporary workaround due to not being able to change comment on existing SEMANTIC VIEW
            create_query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": create_query.add_short_hash(bp.comment),
                },
            )

            self.engine.execute_safe_ddl(create_query)

            return ResolveResult.REPLACE

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl(
            "DROP SEMANTIC VIEW {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_create_semantic_view_sql(self, bp: SemanticViewBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE OR REPLACE SEMANTIC VIEW {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        # ---

        query.append_nl("TABLES (")

        for idx, t in enumerate(bp.tables):
            query.append_nl(
                "  {comma:r}{table_alias:i} AS {table_name:i}",
                {
                    "comma": "  " if idx == 0 else ", ",
                    "table_alias": t.table_alias if t.table_alias else t.table_name.name,
                    "table_name": t.table_name,
                },
            )

            if t.primary_key:
                query.append(
                    "PRIMARY KEY ({col_names:i})",
                    {
                        "col_names": t.primary_key,
                    },
                )

            if t.with_synonyms:
                query.append(
                    "WITH SYNONYMS ({with_synonyms})",
                    {
                        "with_synonyms": t.with_synonyms,
                    },
                )

            if t.comment:
                query.append(
                    "COMMENT = {comment}",
                    {
                        "comment": t.comment,
                    },
                )

        query.append_nl(")")

        # ---

        if bp.relationships:
            query.append_nl("RELATIONSHIPS (")

            for idx, r in enumerate(bp.relationships):
                query.append_nl(
                    "  {comma:r}",
                    {
                        "comma": " " if idx == 0 else ",",
                    },
                )

                if r.relationship_identifier:
                    query.append(
                        "{relationship_identifier:i} AS",
                        {
                            "relationship_identifier": r.relationship_identifier,
                        },
                    )

                query.append(
                    "{table_alias:i} ({columns:i}) REFERENCES {ref_table_alias:i} ({ref_columns:i})",
                    {
                        "table_alias": r.table_alias,
                        "columns": r.columns,
                        "ref_table_alias": r.ref_table_alias,
                        "ref_columns": r.ref_columns,
                    },
                )

            query.append_nl(")")

        # ---

        if bp.facts:
            query.append_nl("FACTS (")

            for idx, e in enumerate(bp.facts):
                query.append_nl(
                    "  {comma:r}{table_alias:i}.{name:i} AS {sql:r}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "table_alias": e.table_alias,
                        "name": e.name,
                        "sql": e.sql,
                    },
                )

                if e.with_synonyms:
                    query.append(
                        "WITH SYNONYMS ({with_synonyms})",
                        {
                            "with_synonyms": e.with_synonyms,
                        },
                    )

                if e.comment:
                    query.append(
                        "COMMENT = {comment}",
                        {
                            "comment": e.comment,
                        },
                    )

            query.append_nl(")")

        # ---

        if bp.dimensions:
            query.append_nl("DIMENSIONS (")

            for idx, e in enumerate(bp.dimensions):
                query.append_nl(
                    "  {comma:r}{table_alias:i}.{name:i} AS {sql:r}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "table_alias": e.table_alias,
                        "name": e.name,
                        "sql": e.sql,
                    },
                )

                if e.with_synonyms:
                    query.append(
                        "WITH SYNONYMS ({with_synonyms})",
                        {
                            "with_synonyms": e.with_synonyms,
                        },
                    )

                if e.comment:
                    query.append(
                        "COMMENT = {comment}",
                        {
                            "comment": e.comment,
                        },
                    )

            query.append_nl(")")

        # ---

        if bp.metrics:
            query.append_nl("METRICS (")

            for idx, e in enumerate(bp.metrics):
                query.append_nl(
                    "  {comma:r}{table_alias:i}.{name:i} AS {sql:r}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "table_alias": e.table_alias,
                        "name": e.name,
                        "sql": e.sql,
                    },
                )

                if e.with_synonyms:
                    query.append(
                        "WITH SYNONYMS ({with_synonyms})",
                        {
                            "with_synonyms": e.with_synonyms,
                        },
                    )

                if e.comment:
                    query.append(
                        "COMMENT = {comment}",
                        {
                            "comment": e.comment,
                        },
                    )

            query.append_nl(")")

        # ---

        # Comment is currently not fully supported due to lack of COMMENT ON SEMANTIC VIEW ... IS
        # As of Apr 2025, it is not possible to change comment of existing semantic view

        return query
