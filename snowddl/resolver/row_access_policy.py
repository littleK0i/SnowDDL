from json import loads

from snowddl.blueprint import RowAccessPolicyBlueprint, ObjectType, Edition, SchemaObjectIdent
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult


class RowAccessPolicyResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True
    skip_min_edition = Edition.ENTERPRISE

    def get_object_type(self) -> ObjectType:
        return ObjectType.ROW_ACCESS_POLICY

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW ROW ACCESS POLICIES IN SCHEMA {database:i}.{schema:i}", {
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
        return self.config.get_blueprints_by_type(RowAccessPolicyBlueprint)

    def create_object(self, bp: RowAccessPolicyBlueprint):
        self._create_policy(bp)
        self._apply_policy_refs(bp, skip_existing=True)

        return ResolveResult.CREATE

    def compare_object(self, bp: RowAccessPolicyBlueprint, row: dict):
        cur = self.engine.execute_meta("DESC ROW ACCESS POLICY {full_name:i}", {
            "full_name": bp.full_name,
        })

        r = cur.fetchone()

        # If signature was changed, policy and all references must be dropped and created again
        if r['signature'] != f"({', '.join([f'{a.name} {a.type.base_type.name}' for a in bp.arguments])})":
            self._drop_policy_refs(bp.full_name)
            self._drop_policy(bp.full_name)

            self._create_policy(bp)
            self._apply_policy_refs(bp, skip_existing=True)

            return ResolveResult.REPLACE

        result = ResolveResult.NOCHANGE

        if self._apply_policy_refs(bp):
            result = ResolveResult.ALTER

        if r['body'] != bp.body:
            self.engine.execute_unsafe_ddl("ALTER ROW ACCESS POLICY {full_name:i} SET BODY -> {body:r}", {
                "full_name": bp.full_name,
                "body": bp.body,
            }, condition=self.engine.settings.execute_row_access_policy)

            result = ResolveResult.ALTER

        if row['comment'] != bp.comment:
            self.engine.execute_unsafe_ddl("ALTER ROW ACCESS POLICY {full_name:i} SET COMMENT = {comment}", {
                "full_name": bp.full_name,
                "comment": bp.comment,
            }, condition=self.engine.settings.execute_row_access_policy)

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self._drop_policy_refs(SchemaObjectIdent('', row['database'], row['schema'], row['name']))
        self._drop_policy(SchemaObjectIdent('', row['database'], row['schema'], row['name']))

        return ResolveResult.DROP

    def _create_policy(self, bp: RowAccessPolicyBlueprint):
        query = self.engine.query_builder()

        query.append("CREATE ROW ACCESS POLICY {full_name:i} AS (", {
            "full_name": bp.full_name,
        })

        for idx, arg in enumerate(bp.arguments):
            query.append_nl("    {comma:r}{arg_name:i} {arg_type:r}", {
                "comma": "  " if idx == 0 else ", ",
                "arg_name": arg.name,
                "arg_type": arg.type,
            })

        query.append_nl(")")

        query.append_nl("RETURNS BOOLEAN -> ")

        query.append_nl("{body:r}", {
            "body": bp.body,
        })

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_row_access_policy)

    def _drop_policy(self, policy_name: SchemaObjectIdent):
        self.engine.execute_unsafe_ddl("DROP ROW ACCESS POLICY {full_name:i}", {
            "full_name": policy_name,
        }, condition=self.engine.settings.execute_row_access_policy)

    def _apply_policy_refs(self, bp: RowAccessPolicyBlueprint, skip_existing=False):
        existing_policy_refs = {} if skip_existing else self._get_existing_policy_refs(bp.full_name)
        applied_change = False

        for ref in bp.references:
            ref_key = f"{ref.object_type.name}|{ref.object_name}|{bp.full_name}"

            # Policy was applied before
            if ref_key in existing_policy_refs:
                existing_ref_columns = existing_policy_refs[ref_key]['columns']
                del(existing_policy_refs[ref_key])

                # Policy was applied to exactly the same columns
                if [str(c) for c in ref.columns] == existing_ref_columns:
                    continue

                # Policy was applied to different columns, should be dropped and re-created
                self.engine.execute_unsafe_ddl("ALTER {object_type:r} {object_name:i} DROP ROW ACCESS POLICY {policy_name:i}", {
                    "object_type": ref.object_type.simplified,
                    "object_name": ref.object_name,
                    "policy_name": bp.full_name,
                }, condition=self.engine.settings.execute_row_access_policy)

            # Apply new policy
            self.engine.execute_unsafe_ddl("ALTER {object_type:r} {object_name:i} ADD ROW ACCESS POLICY {policy_name:i} ON ({columns:i})", {
                "object_type": ref.object_type.simplified,
                "object_name": ref.object_name,
                "policy_name": bp.full_name,
                "columns": ref.columns,
            }, condition=self.engine.settings.execute_row_access_policy)

            applied_change = True

        # Remove remaining policy references which no longer exist in blueprint
        for existing_ref in existing_policy_refs.values():
            self.engine.execute_unsafe_ddl("ALTER {object_type:r} {database:i}.{schema:i}.{name:i} DROP ROW ACCESS POLICY {policy_name:i}", {
                "object_type": existing_ref['object_type'],
                "database": existing_ref['database'],
                "schema": existing_ref['schema'],
                "name": existing_ref['name'],
                "policy_name": bp.full_name,
            }, condition=self.engine.settings.execute_row_access_policy)

            applied_change = True

        return applied_change

    def _drop_policy_refs(self, policy_name: SchemaObjectIdent):
        existing_policy_refs = self._get_existing_policy_refs(policy_name)

        for existing_ref in existing_policy_refs.values():
            self.engine.execute_unsafe_ddl("ALTER {object_type:r} {database:i}.{schema:i}.{name:i} DROP ROW ACCESS POLICY {policy_name:i}", {
                "object_type": existing_ref['object_type'],
                "database": existing_ref['database'],
                "schema": existing_ref['schema'],
                "name": existing_ref['name'],
                "policy_name": policy_name,
            }, condition=self.engine.settings.execute_row_access_policy)

    def _get_existing_policy_refs(self, policy_name: SchemaObjectIdent):
        existing_policy_refs = {}

        cur = self.engine.execute_meta("SELECT * FROM TABLE({database:i}.information_schema.policy_references(policy_name => {policy_name}))", {
            "database": policy_name.database_full_name,
            "policy_name": policy_name,
        })

        for r in cur:
            ref_key = f"{r['REF_ENTITY_DOMAIN']}" \
                      f"|{r['REF_DATABASE_NAME']}.{r['REF_SCHEMA_NAME']}.{r['REF_ENTITY_NAME']}" \
                      f"|{r['POLICY_DB']}.{r['POLICY_SCHEMA']}.{r['POLICY_NAME']}"

            existing_policy_refs[ref_key] = {
                "object_type": r['REF_ENTITY_DOMAIN'],
                "database": r['REF_DATABASE_NAME'],
                "schema": r['REF_SCHEMA_NAME'],
                "name": r['REF_ENTITY_NAME'],
                "columns": loads(r['REF_ARG_COLUMN_NAMES']),
            }

        return existing_policy_refs
