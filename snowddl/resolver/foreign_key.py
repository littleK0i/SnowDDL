from snowddl.blueprint import ForeignKeyBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class ForeignKeyResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.FOREIGN_KEY

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}
        constraints_by_name = {}

        cur = self.engine.execute_meta(
            "SHOW IMPORTED KEYS IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            # Constraint for Hybrid tables are handled separately
            if r["comment"] == ObjectType.HYBRID_TABLE.name:
                continue

            if r["fk_name"] not in constraints_by_name:
                constraints_by_name[r["fk_name"]] = {
                    "database": r["fk_database_name"],
                    "schema": r["fk_schema_name"],
                    "table": r["fk_table_name"],
                    "columns": {r["key_sequence"]: r["fk_column_name"]},
                    "ref_database": r["pk_database_name"],
                    "ref_schema": r["pk_schema_name"],
                    "ref_table": r["pk_table_name"],
                    "ref_columns": {r["key_sequence"]: r["pk_column_name"]},
                }
            else:
                constraints_by_name[r["fk_name"]]["columns"][r["key_sequence"]] = r["fk_column_name"]
                constraints_by_name[r["fk_name"]]["ref_columns"][r["key_sequence"]] = r["pk_column_name"]

        for c in constraints_by_name.values():
            columns_list = [c["columns"][k] for k in sorted(c["columns"])]
            ref_columns_list = [c["ref_columns"][k] for k in sorted(c["ref_columns"])]

            full_name = f"{c['database']}.{c['schema']}.{c['table']}({','.join(columns_list)})"

            existing_objects[full_name] = {
                "database": c["database"],
                "schema": c["schema"],
                "table": c["table"],
                "columns": columns_list,
                "ref_table_name": f"{c['ref_database']}.{c['ref_schema']}.{c['ref_table']}",
                "ref_columns": ref_columns_list,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(ForeignKeyBlueprint)

    def create_object(self, bp: ForeignKeyBlueprint):
        self.engine.execute_safe_ddl(
            "ALTER TABLE {table_name:i} ADD FOREIGN KEY ({columns:i}) REFERENCES {ref_table_name:i} ({ref_columns:i})",
            {
                "table_name": bp.table_name,
                "columns": bp.columns,
                "ref_table_name": bp.ref_table_name,
                "ref_columns": bp.ref_columns,
            },
        )

        return ResolveResult.CREATE

    def compare_object(self, bp: ForeignKeyBlueprint, row: dict):
        if str(bp.ref_table_name) == row["ref_table_name"] and [str(c) for c in bp.ref_columns] == row["ref_columns"]:
            return ResolveResult.NOCHANGE

        self.engine.execute_safe_ddl(
            "ALTER TABLE {table_name:i} DROP FOREIGN KEY ({columns:i})",
            {
                "table_name": bp.table_name,
                "columns": bp.columns,
            },
        )

        self.engine.execute_safe_ddl(
            "ALTER TABLE {table_name:i} ADD FOREIGN KEY ({columns:i}) REFERENCES {ref_table_name:i} ({ref_columns:i})",
            {
                "table_name": bp.table_name,
                "columns": bp.columns,
                "ref_table_name": bp.ref_table_name,
                "ref_columns": bp.ref_columns,
            },
        )

        return ResolveResult.ALTER

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl(
            "ALTER TABLE {database:i}.{schema:i}.{table:i} DROP FOREIGN KEY ({columns:i})",
            {
                "database": row["database"],
                "schema": row["schema"],
                "table": row["table"],
                "columns": row["columns"],
            },
        )

        return ResolveResult.DROP

    def _check_implicit_drop_intention(self, object_full_name: str) -> bool:
        # Dropping any of parent objects implicitly drops this object
        if self.engine.intention_cache.check_parent_object_drop_intention(self.object_type, object_full_name):
            return True

        fk = self.existing_objects[object_full_name]

        for ref_table_object_type in [ObjectType.TABLE, ObjectType.EXTERNAL_TABLE]:
            # Dropping ref_table implicitly drops all foreign keys pointing to it
            if self.engine.intention_cache.check_object_drop_intention(ref_table_object_type, fk["ref_table_name"]):
                return True

            # Dropping any of parent objects of ref_table implicitly drops this object
            if self.engine.intention_cache.check_parent_object_drop_intention(ref_table_object_type, fk["ref_table_name"]):
                return True

        table_full_name = f"{fk['database']}.{fk['schema']}.{fk['table']}"

        # Dropping one of foreign key columns implicitly drops the entire key
        for col_name in fk["columns"]:
            if self.engine.intention_cache.check_column_drop_intention(table_full_name, col_name):
                return True

        # Dropping one of foreign key columns in ref_table implicitly drops the entire key
        for col_name in fk["ref_columns"]:
            if self.engine.intention_cache.check_column_drop_intention(fk["ref_table_name"], col_name):
                return True

        return False
