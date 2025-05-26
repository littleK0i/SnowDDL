from snowddl.blueprint import TableBlueprint, SchemaObjectIdent
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
        clone_source_env_prefix = self.engine.settings.clone_source_env_prefix

        cur = self.engine.execute_meta("SHOW DATABASES")

        for r in cur:
            # Skip shares
            if r["origin"]:
                continue

            src_database = str(r["name"])

            if clone_source_env_prefix:
                # Skip everything which does not start with source prefix
                if not src_database.startswith(clone_source_env_prefix):
                    continue

                dst_database = f"{self.config.env_prefix}{src_database.removeprefix(clone_source_env_prefix)}"
            else:
                dst_database = f"{self.config.env_prefix}{src_database}"

            # Skip every source database without destination database for cloning
            if dst_database not in self.engine.schema_cache.databases:
                continue

            databases_for_clone[dst_database] = {
                "src_database": src_database,
                "dst_database": dst_database,
            }

        return databases_for_clone

    def get_schemas_for_clone(self, database):
        schemas_for_clone = {}

        cur = self.engine.execute_meta(
            "SHOW SCHEMAS IN DATABASE {src_database:i}",
            {
                "src_database": database["src_database"],
            },
        )

        for r in cur:
            # Skip INFORMATION_SCHEMA
            if r["name"] == "INFORMATION_SCHEMA":
                continue

            dst_schema = f"{database['dst_database']}.{r['name']}"

            # Skip every source schema without destination schema for cloning
            if dst_schema not in self.engine.schema_cache.schemas:
                continue

            schemas_for_clone[dst_schema] = {
                "src_database": database["src_database"],
                "dst_database": database["dst_database"],
                "schema": r["name"],
            }

        return schemas_for_clone

    def get_tables_for_clone(self, schema):
        tables_for_clone = {}

        cur = self.engine.execute_meta(
            "SHOW TABLES IN SCHEMA {src_database:i}.{schema:i}",
            {
                "src_database": schema["src_database"],
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

            tables_for_clone[f"{schema['dst_database']}.{r['schema_name']}.{r['name']}"] = {
                "src_database": schema["src_database"],
                "dst_database": schema["dst_database"],
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
            "TABLE IF NOT EXISTS {dst_database:i}.{schema:i}.{name:i}",
            {
                "dst_database": row["dst_database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        query.append_nl(
            "CLONE {src_database:i}.{schema:i}.{name:i}",
            {
                "src_database": row["src_database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        cur = self.engine.execute_clone(query)
        r = cur.fetchone()

        if str(r["status"]).endswith("successfully created."):
            self._drop_existing_policy_refs(
                ObjectType.TABLE, SchemaObjectIdent("", row["dst_database"], row["schema"], row["name"])
            )
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

    def _drop_existing_policy_refs(self, object_type: ObjectType, object_name: SchemaObjectIdent):
        cur = self.engine.execute_meta(
            "SELECT * FROM TABLE(snowflake.information_schema.policy_references(ref_entity_domain => {object_type}, ref_entity_name => {object_name}))",
            {
                "object_type": object_type.singular_for_ref,
                "object_name": object_name,
            },
        )

        for r in cur:
            if r["POLICY_KIND"] == "AGGREGATION_POLICY":
                self.engine.execute_clone(
                    "ALTER {object_type:r} {object_name:i} UNSET AGGREGATION POLICY",
                    {
                        "object_type": object_type.singular_for_ref,
                        "object_name": object_name,
                    },
                )

            elif r["POLICY_KIND"] == "MASKING_POLICY":
                self.engine.execute_clone(
                    "ALTER {object_type:r} {object_name:i} MODIFY COLUMN {column:i} UNSET MASKING POLICY",
                    {
                        "object_type": object_type.singular_for_ref,
                        "object_name": object_name,
                        "column": r["REF_COLUMN_NAME"],
                    },
                )

            elif r["POLICY_KIND"] == "PROJECTION_POLICY":
                self.engine.execute_clone(
                    "ALTER {object_type:r} {object_name:i} MODIFY COLUMN {column:i} UNSET PROJECTION POLICY",
                    {
                        "object_type": object_type.singular_for_ref,
                        "object_name": object_name,
                        "column": r["REF_COLUMN_NAME"],
                    },
                )

            elif r["POLICY_KIND"] == "ROW_ACCESS_POLICY":
                policy_name = SchemaObjectIdent("", r["POLICY_DB"], r["POLICY_SCHEMA"], r["POLICY_NAME"])

                self.engine.execute_clone(
                    "ALTER {object_type:r} {object_name:i} DROP ROW ACCESS POLICY {policy_name:i}",
                    {
                        "object_type": object_type.singular_for_ref,
                        "object_name": object_name,
                        "policy_name": policy_name,
                    },
                )

            else:
                self.engine.logger.warning(
                    f"Detected unknown policy type [{r['POLICY_KIND']} attached to cloned object [{object_name}]"
                )
