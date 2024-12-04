from json import loads

from snowddl.blueprint import AggregationPolicyBlueprint, ObjectType, Edition, SchemaObjectIdent
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult


class AggregationPolicyResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True
    skip_min_edition = Edition.ENTERPRISE

    def get_object_type(self) -> ObjectType:
        return ObjectType.AGGREGATION_POLICY

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW AGGREGATION POLICIES IN SCHEMA {database:i}.{schema:i}",
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
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(AggregationPolicyBlueprint)

    def create_object(self, bp: AggregationPolicyBlueprint):
        self._create_policy(bp)
        self._apply_policy_refs(bp, skip_existing=True)

        return ResolveResult.CREATE

    def compare_object(self, bp: AggregationPolicyBlueprint, row: dict):
        cur = self.engine.execute_meta(
            "DESC AGGREGATION POLICY {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        r = cur.fetchone()
        result = ResolveResult.NOCHANGE

        if self._apply_policy_refs(bp):
            result = ResolveResult.ALTER

        if r["body"] != bp.body:
            self.engine.execute_unsafe_ddl(
                "ALTER AGGREGATION POLICY {full_name:i} SET BODY -> {body:r}",
                {
                    "full_name": bp.full_name,
                    "body": bp.body,
                },
                condition=self.engine.settings.execute_aggregation_policy,
            )

            result = ResolveResult.ALTER

        if row["comment"] != bp.comment:
            self.engine.execute_unsafe_ddl(
                "ALTER AGGREGATION POLICY {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
                condition=self.engine.settings.execute_aggregation_policy,
            )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self._drop_policy_refs(SchemaObjectIdent("", row["database"], row["schema"], row["name"]))
        self._drop_policy(SchemaObjectIdent("", row["database"], row["schema"], row["name"]))

        return ResolveResult.DROP

    def _create_policy(self, bp: AggregationPolicyBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE AGGREGATION POLICY {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        query.append_nl(
            "AS () RETURNS AGGREGATION_CONSTRAINT -> {body:r}",
            {
                "body": bp.body,
            },
        )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_aggregation_policy)

    def _drop_policy(self, policy: SchemaObjectIdent):
        self.engine.execute_unsafe_ddl(
            "DROP AGGREGATION POLICY {full_name:i}",
            {"full_name": policy},
            condition=self.engine.settings.execute_aggregation_policy,
        )

    def _apply_policy_refs(self, bp: AggregationPolicyBlueprint, skip_existing=False):
        existing_policy_refs = {} if skip_existing else self._get_existing_policy_refs(bp.full_name)
        applied_change = False

        for ref in bp.references:
            ref_key = f"{ref.object_type.name}|{ref.object_name}|{bp.full_name}"

            # Policy was applied before
            if ref_key in existing_policy_refs:
                existing_ref_columns = existing_policy_refs[ref_key]["columns"]
                del existing_policy_refs[ref_key]

                # Policy was applied to exactly the same columns
                if [str(c) for c in ref.columns] == existing_ref_columns:
                    continue

            # Apply new policy or replace existing policy with different columns
            query = self.engine.query_builder()

            query.append(
                "ALTER {object_type:r} {object_name:i} SET AGGREGATION POLICY {policy_name:i}",
                {
                    "object_type": ref.object_type.singular_for_ref,
                    "object_name": ref.object_name,
                    "policy_name": bp.full_name,
                },
            )

            if ref.columns:
                query.append(
                    "ENTITY KEY ({columns:i})",
                    {
                        "columns": ref.columns,
                    },
                )

            query.append("FORCE")

            self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_aggregation_policy)
            applied_change = True

        # Remove remaining policy references which no longer exist in blueprint
        for existing_ref in existing_policy_refs.values():
            # TODO: consider use case when object switches to another aggregation policy resolved in parallel
            self.engine.execute_unsafe_ddl(
                "ALTER {object_type:r} {database:i}.{schema:i}.{name:i} UNSET AGGREGATION POLICY",
                {
                    "object_type": existing_ref["object_type"],
                    "database": existing_ref["database"],
                    "schema": existing_ref["schema"],
                    "name": existing_ref["name"],
                },
                condition=self.engine.settings.execute_aggregation_policy,
            )

            applied_change = True

        return applied_change

    def _drop_policy_refs(self, policy_name: SchemaObjectIdent):
        existing_policy_refs = self._get_existing_policy_refs(policy_name)

        for existing_ref in existing_policy_refs.values():
            # TODO: consider use case when object switches to another aggregation policy resolved in parallel
            self.engine.execute_unsafe_ddl(
                "ALTER {object_type:r} {database:i}.{schema:i}.{name:i} UNSET AGGREGATION POLICY",
                {
                    "object_type": existing_ref["object_type"],
                    "database": existing_ref["database"],
                    "schema": existing_ref["schema"],
                    "name": existing_ref["name"],
                },
                condition=self.engine.settings.execute_aggregation_policy,
            )

    def _get_existing_policy_refs(self, policy_name: SchemaObjectIdent):
        existing_policy_refs = {}

        cur = self.engine.execute_meta(
            "SELECT * FROM TABLE(snowflake.information_schema.policy_references(policy_name => {policy_name}))",
            {
                "policy_name": policy_name,
            },
        )

        for r in cur:
            ref_key = (
                f"{r['REF_ENTITY_DOMAIN']}"
                f"|{r['REF_DATABASE_NAME']}.{r['REF_SCHEMA_NAME']}.{r['REF_ENTITY_NAME']}"
                f"|{r['POLICY_DB']}.{r['POLICY_SCHEMA']}.{r['POLICY_NAME']}"
            )

            existing_policy_refs[ref_key] = {
                "object_type": r["REF_ENTITY_DOMAIN"],
                "database": r["REF_DATABASE_NAME"],
                "schema": r["REF_SCHEMA_NAME"],
                "name": r["REF_ENTITY_NAME"],
                "columns": loads(r["REF_ARG_COLUMN_NAMES"]) if r["REF_ARG_COLUMN_NAMES"] else [],
            }

        return existing_policy_refs
