from snowddl.blueprint import StageBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType

class StageResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.STAGE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW STAGES IN SCHEMA {database:i}.{schema:i}", {
            "database": schema['database'],
            "schema": schema['schema'],
        })

        for r in cur:
            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r['database_name'],
                "schema": r['schema_name'],
                "name": r['name'],
                "url": r['url'],
                "storage_integration": r['storage_integration'],
                "owner": r['owner'],
                "type": r['type'],
                "comment": r['comment'],
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(StageBlueprint)

    def create_object(self, bp: StageBlueprint):
        common_query = self._build_common_stage_sql(bp)
        create_query = self.engine.query_builder()

        create_query.append("CREATE STAGE {full_name:i}", {
            "full_name": bp.full_name,
        })

        create_query.append(common_query)

        self.engine.execute_safe_ddl(create_query)

        self.engine.execute_safe_ddl("COMMENT ON STAGE {full_name:i} IS {comment}", {
            "full_name": bp.full_name,
            "comment": common_query.add_short_hash(bp.comment),
        })

        return ResolveResult.CREATE

    def compare_object(self, bp: StageBlueprint, row: dict):
        common_query = self._build_common_stage_sql(bp)

        if not common_query.compare_short_hash(row['comment']):
            alter_query = self.engine.query_builder()

            alter_query.append("ALTER STAGE {full_name:i} SET", {
                "full_name": bp.full_name,
            })

            alter_query.append(common_query)

            self.engine.execute_safe_ddl(alter_query)

            self.engine.execute_safe_ddl("COMMENT ON STAGE {full_name:i} IS {comment}", {
                "full_name": bp.full_name,
                "comment": common_query.add_short_hash(bp.comment),
            })

            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl("DROP STAGE {database:i}.{schema:i}.{name:i}", {
            "database": row['database'],
            "schema": row['schema'],
            "name": row['name'],
        })

        return ResolveResult.DROP

    def _build_common_stage_sql(self, bp: StageBlueprint):
        query = self.engine.query_builder()

        if bp.url:
            query.append_nl("URL = {url}", {
                "url": bp.url
            })

        if bp.storage_integration:
            query.append_nl("STORAGE_INTEGRATION = {storage_integration:i}", {
                "storage_integration": bp.storage_integration,
            })

        if bp.encryption:
            query.append_nl("ENCRYPTION = (")

            for k, v in bp.encryption.items():
                query.append("{param_name:r} = {param_value:dp}", {
                    "param_name": k,
                    "param_value": v,
                })

            query.append(")")

        if bp.directory:
            query.append_nl("DIRECTORY = (")

            for k, v in bp.directory.items():
                query.append("{param_name:r} = {param_value:dp}", {
                    "param_name": k,
                    "param_value": v,
                })

            query.append(")")

        if bp.file_format:
            query.append_nl("FILE_FORMAT = (FORMAT_NAME = {file_format:i})", {
                "file_format": bp.file_format,
            })

        if bp.copy_options:
            query.append_nl("COPY_OPTIONS = (")

            for k, v in bp.copy_options.items():
                query.append("{option_name:r} = {option_value:dp}", {
                    "option_name": k,
                    "option_value": v,
                })

            query.append(")")

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        return query
