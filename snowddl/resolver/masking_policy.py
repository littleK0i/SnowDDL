from snowddl.blueprint import MaskingPolicyBlueprint, ObjectType, Edition, SchemaObjectIdent
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult


class MaskingPolicyResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True
    skip_min_edition = Edition.ENTERPRISE

    def get_object_type(self) -> ObjectType:
        return ObjectType.MASKING_POLICY

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW MASKING POLICIES IN SCHEMA {database:i}.{schema:i}", {
            "database": schema['database'],
            "schema": schema['schema'],
        })

        for r in cur:
            full_name = f"{r['database_name']}.{r['schema_name']}.{r['name']}"

            existing_objects[full_name] = {
                "database": r['database_name'],
                "schema": r['schema_name'],
                "name": r['name'],
                "comment": r['comment'] if r['comment'] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(MaskingPolicyBlueprint)

    def create_object(self, bp: MaskingPolicyBlueprint):
        self._create_policy(bp)
        self._apply_policy_refs(bp, skip_existing=True)

        return ResolveResult.CREATE

    def compare_object(self, bp: MaskingPolicyBlueprint, row: dict):
        cur = self.engine.execute_meta("DESC MASKING POLICY {full_name:i}", {
            "full_name": bp.full_name,
        })

        r = cur.fetchone()

        # If signature or return type was changed, policy and all references must be dropped and created again
        if r['signature'] != f"({', '.join([f'{a.name} {a.type.base_type.name}' for a in bp.arguments])})" \
        or r['return_type'] != str(bp.returns):
            self._drop_policy_refs(bp.full_name)
            self._drop_policy(bp.full_name)

            self._create_policy(bp)
            self._apply_policy_refs(bp, skip_existing=True)

            return ResolveResult.REPLACE

        result = ResolveResult.NOCHANGE

        if self._apply_policy_refs(bp):
            result = ResolveResult.ALTER

        if r['body'] != bp.body:
            self.engine.execute_unsafe_ddl("ALTER MASKING POLICY {full_name:i} SET BODY -> {body:r}", {
                "full_name": bp.full_name,
                "body": bp.body,
            }, condition=self.engine.settings.execute_masking_policy)

            result = ResolveResult.ALTER

        if row['comment'] != bp.comment:
            self.engine.execute_unsafe_ddl("ALTER MASKING POLICY {full_name:i} SET COMMENT = {comment}", {
                "full_name": bp.full_name,
                "comment": bp.comment,
            }, condition=self.engine.settings.execute_masking_policy)

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self._drop_policy_refs(SchemaObjectIdent('', row['database'], row['schema'], row['name']))
        self._drop_policy(SchemaObjectIdent('', row['database'], row['schema'], row['name']))

        return ResolveResult.DROP

    def _create_policy(self, bp: MaskingPolicyBlueprint):
        query = self.engine.query_builder()

        query.append("CREATE MASKING POLICY {full_name:i} AS (", {
            "full_name": bp.full_name,
        })

        for idx, arg in enumerate(bp.arguments):
            query.append_nl("    {comma:r}{arg_name:i} {arg_type:r}", {
                "comma": "  " if idx == 0 else ", ",
                "arg_name": arg.name,
                "arg_type": arg.type,
            })

        query.append_nl(")")

        query.append_nl("RETURNS {ret_type:r} -> ", {
            "ret_type": bp.returns,
        })

        query.append_nl("{body:r}", {
            "body": bp.body,
        })

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_masking_policy)

    def _drop_policy(self, policy: SchemaObjectIdent):
        self.engine.execute_unsafe_ddl("DROP MASKING POLICY {full_name:i}", {
            "full_name": policy
        }, condition=self.engine.settings.execute_masking_policy)

    def _apply_policy_refs(self, bp: MaskingPolicyBlueprint, skip_existing=False):
        existing_policy_refs = {} if skip_existing else self._get_existing_policy_refs(bp.full_name)
        applied_change = False

        for ref in bp.references:
            ref_key = f"{ref.object_type.name}|{ref.object_name}|{ref.columns[0]}"

            # Policy was applied before
            if ref_key in existing_policy_refs:
                del(existing_policy_refs[ref_key])
                continue

            # Apply new masking policy
            self.engine.execute_unsafe_ddl("ALTER {object_type:r} {object_name:i} MODIFY COLUMN {first_column:i} SET MASKING POLICY {policy_name:i} USING ({columns:i})", {
                "object_type": ref.object_type.singular,
                "object_name": ref.object_name,
                "policy_name": bp.full_name,
                "first_column": ref.columns[0],
                "columns": ref.columns,
            }, condition=self.engine.settings.execute_masking_policy)

            applied_change = True

        # Remove remaining policy references which no longer exist in blueprint
        for existing_ref in existing_policy_refs.values():
            self.engine.execute_unsafe_ddl("ALTER {object_type:r} {database:i}.{schema:i}.{name:i} MODIFY COLUMN {first_column:i} UNSET MASKING POLICY", {
                "object_type": existing_ref['object_type'],
                "database": existing_ref['database'],
                "schema": existing_ref['schema'],
                "name": existing_ref['name'],
                "first_column": existing_ref['first_column'],
            }, condition=self.engine.settings.execute_masking_policy)

            applied_change = True

        return applied_change

    def _drop_policy_refs(self, policy_name: SchemaObjectIdent):
        existing_policy_refs = self._get_existing_policy_refs(policy_name)

        for existing_ref in existing_policy_refs.values():
            self.engine.execute_unsafe_ddl("ALTER {object_type:r} {database:i}.{schema:i}.{name:i} MODIFY COLUMN {first_column:i} UNSET MASKING POLICY", {
                "object_type": existing_ref['object_type'],
                "database": existing_ref['database'],
                "schema": existing_ref['schema'],
                "name": existing_ref['name'],
                "first_column": existing_ref['first_column'],
            }, condition=self.engine.settings.execute_masking_policy)

    def _get_existing_policy_refs(self, policy_name: SchemaObjectIdent):
        existing_policy_refs = {}

        cur = self.engine.execute_meta("SELECT * FROM TABLE({database:i}.information_schema.policy_references(policy_name => {policy_name}))", {
            "database": policy_name.database_full_name,
            "policy_name": policy_name,
        })

        for r in cur:
            ref_key = f"{r['REF_ENTITY_DOMAIN']}|{r['REF_DATABASE_NAME']}.{r['REF_SCHEMA_NAME']}.{r['REF_ENTITY_NAME']}|{r['REF_COLUMN_NAME']}"

            existing_policy_refs[ref_key] = {
                "object_type": r['REF_ENTITY_DOMAIN'],
                "database": r['REF_DATABASE_NAME'],
                "schema": r['REF_SCHEMA_NAME'],
                "name": r['REF_ENTITY_NAME'],
                "first_column": r['REF_COLUMN_NAME'],
            }

        return existing_policy_refs
