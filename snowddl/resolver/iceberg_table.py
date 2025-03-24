from snowddl.blueprint import IcebergTableBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class IcebergTableResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.ICEBERG_TABLE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW ICEBERG TABLES IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            # Currently only external iceberg tables are supported
            if r["iceberg_table_type"] != "UNMANAGED":
                continue

            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "owner": r["owner"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(IcebergTableBlueprint)

    def create_object(self, bp: IcebergTableBlueprint):
        create_query = self.engine.query_builder()
        common_query = self._build_common_unmanaged_iceberg_table_sql(bp)

        create_query.append(
            "CREATE ICEBERG TABLE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        create_query.append_nl(common_query)

        self.engine.execute_safe_ddl(create_query)
        self.engine.execute_safe_ddl(
            "ALTER ICEBERG TABLE {full_name:i} SET COMMENT = {comment}",
            {
                "full_name": bp.full_name,
                "comment": common_query.add_short_hash(bp.comment),
            },
        )

        return ResolveResult.CREATE

    def compare_object(self, bp: IcebergTableBlueprint, row: dict):
        replace_query = self.engine.query_builder()
        common_query = self._build_common_unmanaged_iceberg_table_sql(bp)

        if not common_query.compare_short_hash(row["comment"]):
            replace_query.append(
                "CREATE OR REPLACE ICEBERG TABLE {full_name:i}",
                {
                    "full_name": bp.full_name,
                },
            )

            replace_query.append_nl(common_query)

            self.engine.execute_safe_ddl(replace_query)
            self.engine.execute_safe_ddl(
                "ALTER ICEBERG TABLE {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": common_query.add_short_hash(bp.comment),
                },
            )

            return ResolveResult.REPLACE

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP ICEBERG TABLE {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_common_unmanaged_iceberg_table_sql(self, bp: IcebergTableBlueprint):
        query = self.engine.query_builder()

        query.append_nl(
            "EXTERNAL_VOLUME = {external_volume:i}",
            {
                "external_volume": bp.external_volume,
            },
        )

        query.append_nl(
            "CATALOG = {catalog:i}",
            {
                "catalog": bp.catalog,
            },
        )

        if bp.catalog_table_name:
            query.append_nl(
                "CATALOG_TABLE_NAME = {catalog_table_name}",
                {
                    "catalog_table_name": bp.catalog_table_name,
                },
            )

        if bp.catalog_namespace:
            query.append_nl(
                "CATALOG_NAMESPACE = {catalog_namespace}",
                {
                    "catalog_namespace": bp.catalog_namespace,
                },
            )

        if bp.metadata_file_path:
            query.append_nl(
                "METADATA_FILE_PATH = {metadata_file_path}",
                {
                    "metadata_file_path": bp.metadata_file_path,
                },
            )

        if bp.base_location:
            query.append_nl(
                "BASE_LOCATION = {base_location}",
                {
                    "base_location": bp.base_location,
                },
            )

        if bp.replace_invalid_characters:
            query.append_nl("REPLACE_INVALID_CHARACTERS = TRUE")

        if bp.auto_refresh:
            query.append_nl("AUTO_REFRESH = TRUE")

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {"comment": bp.comment})

        return query
