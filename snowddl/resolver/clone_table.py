from snowddl.blueprint import TableBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractResolver, ResolveResult, ObjectType


class CloneTableResolver(AbstractResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.CLONE_TABLE

    def get_blueprints(self):
        return {}

    def get_existing_objects(self):
        databases_for_clone = self.get_databases_for_clone()
        schemas_for_clone = {}
        tables_for_clone = {}

        # Get schemas for clone in parallel
        for schema_objects in self.engine.executor.map(self.get_schemas_for_clone, databases_for_clone.values()):
            schemas_for_clone.update(schema_objects)

        # Get tables for clone in parallel
        for table_objects in self.engine.executor.map(self.get_tables_for_clone, schemas_for_clone.values()):
            tables_for_clone.update(table_objects)

        return tables_for_clone

    def get_databases_for_clone(self):
        databases_for_clone = {}

        cur = self.engine.execute_meta("SHOW DATABASES")

        for r in cur:
            # Skip shares
            if r["origin"]:
                continue

            # Skip databases without destination for cloning
            if f"{self.config.env_prefix}{r['name']}" not in self.engine.schema_cache.databases:
                continue

            databases_for_clone[r["name"]] = {
                "database": r["name"],
            }

        return databases_for_clone

    def get_schemas_for_clone(self, database):
        schemas_for_clone = {}

        cur = self.engine.execute_meta(
            "SHOW SCHEMAS IN DATABASE {database:i}",
            {
                "database": database["database"],
            },
        )

        for r in cur:
            # Skip INFORMATION_SCHEMA
            if r["name"] == "INFORMATION_SCHEMA":
                continue

            # Skip schemas without destination for cloning
            if f"{self.config.env_prefix}{r['database_name']}.{r['name']}" not in self.engine.schema_cache.schemas:
                continue

            schemas_for_clone[f"{r['database_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["name"],
            }

        return schemas_for_clone

    def get_tables_for_clone(self, schema):
        tables_for_clone = {}

        cur = self.engine.execute_meta(
            "SHOW TABLES IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            # Skip other table types
            if (
                r.get("is_external") == "Y"
                or r.get("is_event") == "Y"
                or r.get("is_hybrid") == "Y"
                or r.get("is_iceberg") == "Y"
                or r.get("is_dynamic") == "Y"
            ):
                continue

            tables_for_clone[f"{self.config.env_prefix}{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "is_transient": r["kind"] == "TRANSIENT",
            }

        return tables_for_clone

    def create_object(self, bp: TableBlueprint):
        return ResolveResult.NOCHANGE

    def compare_object(self, bp: TableBlueprint, row: dict):
        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        # Drop object is utilized since we have no blueprints for clones, but only existing objects
        # All such objects should be "dropped" from AbstractResolver perspective
        # TODO: find more elegant solution if cloning becomes popular

        query = self.engine.query_builder()
        query.append("CREATE")

        if row["is_transient"]:
            query.append("TRANSIENT")

        query.append(
            "TABLE IF NOT EXISTS {database_with_prefix:i}.{schema:i}.{table_name:i}",
            {
                "database_with_prefix": f"{self.config.env_prefix}{row['database']}",
                "schema": row["schema"],
                "table_name": row["name"],
            },
        )

        query.append_nl(
            "CLONE {database:i}.{schema:i}.{table_name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "table_name": row["name"],
            },
        )

        cur = self.engine.execute_clone(query)
        r = cur.fetchone()

        if str(r["status"]).endswith("successfully created."):
            return ResolveResult.CREATE

        return ResolveResult.NOCHANGE

    def destroy(self):
        pass

    def _is_skipped(self):
        if not self.engine.settings.clone_table:
            return True

        if super()._is_skipped():
            return True

        return False
