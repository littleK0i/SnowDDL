from snowddl.blueprint import SequenceBlueprint
from snowddl.error import SnowDDLUnsupportedError
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class SequenceResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.SEQUENCE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW SEQUENCES IN SCHEMA {database:i}.{schema:i}",
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
                "next_value": r["next_value"],
                "interval": r["interval"],
                "ordered": bool(r["ordered"] == "Y"),
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(SequenceBlueprint)

    def create_object(self, bp: SequenceBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE SEQUENCE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        query.append_nl(
            "START = {start:d}",
            {
                "start": bp.start,
            },
        )

        query.append_nl(
            "INCREMENT = {interval:d}",
            {
                "interval": bp.interval,
            },
        )

        if bp.is_ordered is True:
            query.append_nl("ORDER")
        elif bp.is_ordered is False:
            query.append_nl("NOORDER")

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        self.engine.execute_safe_ddl(query)

        return ResolveResult.CREATE

    def compare_object(self, bp: SequenceBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if bp.interval != row["interval"]:
            self.engine.execute_safe_ddl(
                "ALTER SEQUENCE {full_name:i} SET INCREMENT = {interval:d}",
                {
                    "full_name": bp.full_name,
                    "interval": bp.interval,
                },
            )

            result = ResolveResult.ALTER

        if bp.is_ordered is not None and bp.is_ordered != row["ordered"]:
            if bp.is_ordered is False:
                self.engine.execute_safe_ddl(
                    "ALTER SEQUENCE {full_name:i} SET NOORDER",
                    {
                        "full_name": bp.full_name,
                    },
                )
            else:
                raise SnowDDLUnsupportedError("Cannot change NOORDER sequence to ORDER")

        if bp.comment != row["comment"]:
            self.engine.execute_safe_ddl(
                "ALTER SEQUENCE {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
            )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP SEQUENCE {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP
