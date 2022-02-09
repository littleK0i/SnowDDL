from snowddl.blueprint import FileFormatBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class FileFormatResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.FILE_FORMAT

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW FILE FORMATS IN SCHEMA {database:i}.{schema:i}", {
            "database": schema['database'],
            "schema": schema['schema'],
        })

        for r in cur:
            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r['database_name'],
                "schema": r['schema_name'],
                "name": r['name'],
                "owner": r['owner'],
                "type": r['type'],
                "format_options": r['format_options'],
                "comment": r['comment'],
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(FileFormatBlueprint)

    def create_object(self, bp: FileFormatBlueprint):
        query = self._build_create_file_format(bp)

        self.engine.execute_safe_ddl(query)

        self.engine.execute_safe_ddl("COMMENT ON FILE FORMAT {full_name:i} IS {comment}", {
            "full_name": bp.full_name,
            "comment": query.add_short_hash(bp.comment),
        })

        return ResolveResult.CREATE

    def compare_object(self, bp: FileFormatBlueprint, row: dict):
        query = self._build_create_file_format(bp)

        if not query.compare_short_hash(row['comment']):
            self.engine.execute_safe_ddl(query)

            self.engine.execute_safe_ddl("COMMENT ON FILE FORMAT {full_name:i} IS {comment}", {
                "full_name": bp.full_name,
                "comment": query.add_short_hash(bp.comment),
            })

            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl("DROP FILE FORMAT {database:i}.{schema:i}.{name:i}", {
            "database": row['database'],
            "schema": row['schema'],
            "name": row['name'],
        })

        return ResolveResult.DROP

    def _build_create_file_format(self, bp: FileFormatBlueprint):
        query = self.engine.query_builder()

        query.append("CREATE FILE FORMAT {full_name:i}", {
            "full_name": bp.full_name,
        })

        query.append_nl("TYPE = {type}", {
            "type": bp.type,
        })

        for option_name, option_value in bp.format_options.items():
            query.append_nl("{option_name:r} = {option_value:dp}", {
                "option_name": option_name,
                "option_value": option_value,
            })

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        return query
