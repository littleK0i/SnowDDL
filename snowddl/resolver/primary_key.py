from snowddl.blueprint import PrimaryKeyBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class PrimaryKeyResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.PRIMARY_KEY

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}
        constraints_by_name = {}

        cur = self.engine.execute_meta(
            "SHOW PRIMARY KEYS IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            # Constraint for Hybrid tables are handled separately
            if r["comment"] == ObjectType.HYBRID_TABLE.name:
                continue

            if r["constraint_name"] not in constraints_by_name:
                constraints_by_name[r["constraint_name"]] = {
                    "database": r["database_name"],
                    "schema": r["schema_name"],
                    "table": r["table_name"],
                    "columns": {r["key_sequence"]: r["column_name"]},
                }
            else:
                constraints_by_name[r["constraint_name"]]["columns"][r["key_sequence"]] = r["column_name"]

        for c in constraints_by_name.values():
            columns_list = [c["columns"][k] for k in sorted(c["columns"])]
            full_name = f"{c['database']}.{c['schema']}.{c['table']}"

            existing_objects[full_name] = {
                "database": c["database"],
                "schema": c["schema"],
                "table": c["table"],
                "columns": columns_list,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(PrimaryKeyBlueprint)

    def create_object(self, bp: PrimaryKeyBlueprint):
        self.engine.execute_safe_ddl(
            "ALTER TABLE {table_name:i} ADD PRIMARY KEY ({columns:i})",
            {
                "table_name": bp.table_name,
                "columns": bp.columns,
            },
        )

        return ResolveResult.CREATE

    def compare_object(self, bp: PrimaryKeyBlueprint, row: dict):
        if [str(c) for c in bp.columns] == row["columns"]:
            return ResolveResult.NOCHANGE

        self.engine.execute_safe_ddl(
            "ALTER TABLE {table_name:i} DROP PRIMARY KEY",
            {
                "table_name": bp.table_name,
            },
        )

        self.engine.execute_safe_ddl(
            "ALTER TABLE {table_name:i} ADD PRIMARY KEY ({columns:i})",
            {
                "table_name": bp.table_name,
                "columns": bp.columns,
            },
        )

        return ResolveResult.ALTER

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl(
            "ALTER TABLE {database:i}.{schema:i}.{table:i} DROP PRIMARY KEY",
            {
                "database": row["database"],
                "schema": row["schema"],
                "table": row["table"],
            },
        )

        return ResolveResult.DROP
