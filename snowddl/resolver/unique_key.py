from snowddl.blueprint import UniqueKeyBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class UniqueKeyResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.UNIQUE_KEY

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}
        constraints_by_name = {}

        cur = self.engine.execute_meta("SHOW UNIQUE KEYS IN SCHEMA {database:i}.{schema:i}", {
            "database": schema['database'],
            "schema": schema['schema'],
        })

        for r in cur:
            if r['constraint_name'] not in constraints_by_name:
                constraints_by_name[r['constraint_name']] = {
                    "database": r['database_name'],
                    "schema": r['schema_name'],
                    "table": r['table_name'],
                    "columns": {r['key_sequence']: r['column_name']}
                }
            else:
                constraints_by_name[r['constraint_name']]['columns'][r['key_sequence']] = r['column_name']

        for c in constraints_by_name.values():
            columns_list = [c['columns'][k] for k in sorted(c['columns'])]
            full_name = f"{c['database']}.{c['schema']}.{c['table']}({','.join(columns_list)})"

            existing_objects[full_name] = {
                "database": c['database'],
                "schema": c['schema'],
                "table": c['table'],
                "columns": columns_list,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(UniqueKeyBlueprint)

    def create_object(self, bp: UniqueKeyBlueprint):
        self.engine.execute_safe_ddl("ALTER TABLE {table_name:i} ADD UNIQUE ({columns:i})", {
            "table_name": bp.table_name,
            "columns": bp.columns,
        })

        return ResolveResult.CREATE

    def compare_object(self, bp: UniqueKeyBlueprint, row: dict):
        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl("ALTER TABLE {database:i}.{schema:i}.{table:i} DROP UNIQUE ({columns:i})", {
            "database": row['database'],
            "schema": row['schema'],
            "table": row['table'],
            "columns": row['columns'],
        })

        return ResolveResult.DROP
