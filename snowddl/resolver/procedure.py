from snowddl.blueprint import ProcedureBlueprint, ComplexIdentWithPrefixAndArgs
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType
from snowddl.resolver._utils import dtypes_from_arguments


class ProcedureResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.PROCEDURE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW PROCEDURES IN SCHEMA {database:i}.{schema:i}", {
            "database": schema['database'],
            "schema": schema['schema'],
        })

        for r in cur:
            full_name = f"{r['catalog_name']}.{r['schema_name']}.{r['name']}({dtypes_from_arguments(r['arguments'])})"

            existing_objects[full_name] = {
                "database": r['catalog_name'],
                "schema": r['schema_name'],
                "name": r['name'],
                "arguments": r['arguments'],
                "comment": r['description'],
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(ProcedureBlueprint)

    def create_object(self, bp: ProcedureBlueprint):
        query = self._build_create_procedure(bp)

        self.engine.execute_safe_ddl(query)

        self.engine.execute_safe_ddl("COMMENT ON PROCEDURE {full_name:i} IS {comment}", {
            "full_name": bp.full_name,
            "comment": query.add_short_hash(bp.comment),
        })

        return ResolveResult.CREATE

    def compare_object(self, bp: ProcedureBlueprint, row: dict):
        query = self._build_create_procedure(bp)

        if not query.compare_short_hash(row['comment']):
            self.engine.execute_safe_ddl(query)

            self.engine.execute_safe_ddl("COMMENT ON PROCEDURE {full_name:i} IS {comment}", {
                "full_name": bp.full_name,
                "comment": query.add_short_hash(bp.comment),
            })

            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl("DROP PROCEDURE {database:i}.{schema:i}.{name:i}({dtypes:r})", {
            "database": row['database'],
            "schema": row['schema'],
            "name": row['name'],
            "dtypes": dtypes_from_arguments(row['arguments']),
        })

        return ResolveResult.DROP

    def _build_create_procedure(self, bp: ProcedureBlueprint):
        query = self.engine.query_builder()

        query.append("CREATE OR REPLACE PROCEDURE {database:i}.{schema:i}.{name:i} (", {
            "database": bp.database,
            "schema": bp.schema,
            "name": bp.name,
        })

        for idx, arg in enumerate(bp.arguments):
            query.append_nl("    {comma:r}{arg_name:i} {arg_type:r}", {
                "comma": "  " if idx == 0 else ", ",
                "arg_name": arg.name,
                "arg_type": arg.type,
            })

        query.append_nl(")")

        query.append_nl("RETURNS {ret_type:r}", {
            "ret_type": bp.returns,
        })

        query.append_nl("LANGUAGE {language:r}", {
            "language": bp.language,
        })

        if bp.is_strict:
            query.append_nl("STRICT")

        if bp.is_immutable:
            query.append_nl("IMMUTABLE")

        if bp.is_execute_as_caller:
            query.append_nl("EXECUTE AS CALLER")

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        query.append_nl("AS {body}", {
            "body": bp.body,
        })

        return query
