from snowddl.blueprint import FileFormatBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class FileFormatResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.FILE_FORMAT

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW FILE FORMATS IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "owner": r["owner"],
                "type": r["type"],
                "format_options": r["format_options"],
                "comment": r["comment"],
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(FileFormatBlueprint)

    def create_object(self, bp: FileFormatBlueprint):
        common_query = self._build_common_file_format_sql(bp)
        create_query = self.engine.query_builder()

        create_query.append(
            "CREATE FILE FORMAT {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        create_query.append(common_query)

        self.engine.execute_safe_ddl(create_query)

        self.engine.execute_safe_ddl(
            "COMMENT ON FILE FORMAT {full_name:i} IS {comment}",
            {
                "full_name": bp.full_name,
                "comment": common_query.add_short_hash(bp.comment),
            },
        )

        return ResolveResult.CREATE

    def compare_object(self, bp: FileFormatBlueprint, row: dict):
        common_query = self._build_common_file_format_sql(bp)

        if not common_query.compare_short_hash(row["comment"]):
            alter_query = self.engine.query_builder()

            if bp.type != row["type"]:
                # Format type cannot be changed with ALTER, must re-create the format entirely
                alter_query.append(
                    "CREATE OR REPLACE FILE FORMAT {full_name:i}",
                    {
                        "full_name": bp.full_name,
                    },
                )

                result = ResolveResult.REPLACE
            else:
                # Individual format settings can be changed with ALTER
                alter_query.append(
                    "ALTER FILE FORMAT {full_name:i} SET",
                    {
                        "full_name": bp.full_name,
                    },
                )

                result = ResolveResult.ALTER

            alter_query.append(common_query)

            self.engine.execute_safe_ddl(alter_query)

            self.engine.execute_safe_ddl(
                "COMMENT ON FILE FORMAT {full_name:i} IS {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": common_query.add_short_hash(bp.comment),
                },
            )

            return result

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl(
            "DROP FILE FORMAT {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_common_file_format_sql(self, bp: FileFormatBlueprint):
        query = self.engine.query_builder()

        query.append_nl(
            "TYPE = {type}",
            {
                "type": bp.type,
            },
        )

        for option_name, option_value in bp.format_options.items():
            query.append_nl(
                "{option_name:r} = {option_value:dp}",
                {
                    "option_name": option_name,
                    "option_value": option_value,
                },
            )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        return query
