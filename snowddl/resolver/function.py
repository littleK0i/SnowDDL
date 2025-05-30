from snowddl.blueprint import FunctionBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType
from snowddl.resolver._utils import dtypes_from_arguments


class FunctionResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.FUNCTION

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW USER FUNCTIONS IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            if r["is_external_function"] == "Y" or r["is_data_metric"] == "Y":
                continue

            full_name = f"{r['catalog_name']}.{r['schema_name']}.{r['name']}({dtypes_from_arguments(r['arguments'])})"

            existing_objects[full_name] = {
                "database": r["catalog_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "arguments": r["arguments"],
                "comment": r["description"],
                "is_aggregate": r["is_aggregate"] == "Y",
                "is_table_function": r["is_table_function"] == "Y",
                "is_secure": r["is_secure"] == "Y",
                "is_memoizable": r["is_memoizable"] == "Y",
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(FunctionBlueprint)

    def create_object(self, bp: FunctionBlueprint):
        query = self._build_create_function(bp)

        self.engine.execute_safe_ddl(query)

        self.engine.execute_safe_ddl(
            "COMMENT ON FUNCTION {full_name:i} IS {comment}",
            {
                "full_name": bp.full_name,
                "comment": query.add_short_hash(bp.comment),
            },
        )

        return ResolveResult.CREATE

    def compare_object(self, bp: FunctionBlueprint, row: dict):
        query = self._build_create_function(bp)

        if not query.compare_short_hash(row["comment"]):
            self.engine.execute_safe_ddl(query)

            self.engine.execute_safe_ddl(
                "COMMENT ON FUNCTION {full_name:i} IS {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": query.add_short_hash(bp.comment),
                },
            )

            return ResolveResult.REPLACE

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl(
            "DROP FUNCTION {database:i}.{schema:i}.{name:i}({dtypes:r})",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
                "dtypes": dtypes_from_arguments(row["arguments"]),
            },
        )

        return ResolveResult.DROP

    def _build_create_function(self, bp: FunctionBlueprint):
        query = self.engine.query_builder()
        query.append("CREATE OR REPLACE")

        if bp.is_secure:
            query.append("SECURE")

        if bp.is_aggregate:
            query.append("AGGREGATE")

        query.append(
            "FUNCTION {full_name:in} (",
            {
                "full_name": bp.full_name,
            },
        )

        for idx, arg in enumerate(bp.arguments):
            query.append_nl(
                "    {comma:r}{arg_name:i} {arg_type:r}",
                {
                    "comma": "  " if idx == 0 else ", ",
                    "arg_name": arg.name,
                    "arg_type": arg.type,
                },
            )

            if arg.default:
                query.append(
                    "DEFAULT {default:r}",
                    {
                        "default": arg.default,
                    },
                )

        query.append_nl(")")

        if isinstance(bp.returns, list):
            query.append_nl("RETURNS TABLE (")

            for idx, arg in enumerate(bp.returns):
                query.append_nl(
                    "    {comma:r}{ret_name:i} {ret_type:r}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "ret_name": arg.name,
                        "ret_type": arg.type,
                    },
                )

            query.append_nl(")")
        else:
            query.append_nl(
                "RETURNS {ret_type:r}",
                {
                    "ret_type": bp.returns,
                },
            )

        query.append_nl(
            "LANGUAGE {language:r}",
            {
                "language": bp.language,
            },
        )

        if bp.is_strict:
            query.append_nl("STRICT")

        if bp.is_immutable:
            query.append_nl("IMMUTABLE")

        if bp.is_memoizable:
            query.append_nl("MEMOIZABLE")

        if bp.runtime_version:
            query.append_nl(
                "RUNTIME_VERSION = {runtime_version}",
                {
                    "runtime_version": bp.runtime_version,
                },
            )

        if bp.imports:
            query.append_nl("IMPORTS = ({imports})", {"imports": [f"@{i.stage_name}{i.path}" for i in bp.imports]})

        if bp.packages:
            query.append_nl(
                "PACKAGES = ({packages})",
                {
                    "packages": bp.packages,
                },
            )

        if bp.handler:
            query.append_nl(
                "HANDLER = {handler}",
                {
                    "handler": bp.handler,
                },
            )

        if bp.external_access_integrations:
            # Snowflake bug: EXTERNAL_ACCESS_INTEGRATIONS must be identifiers
            # It does not accept identifiers in double-quotes
            query.append_nl(
                "EXTERNAL_ACCESS_INTEGRATIONS = ({external_access_integrations:r})",
                {
                    "external_access_integrations": bp.external_access_integrations,
                },
            )

        if bp.secrets:
            query.append_nl("SECRETS = (")

            for idx, (var_name, secret_name) in enumerate(bp.secrets.items()):
                query.append(
                    "{comma:r}{var_name} = {secret_name:i}",
                    {
                        "comma": "" if idx == 0 else ", ",
                        "var_name": var_name,
                        "secret_name": secret_name,
                    },
                )

            query.append(")")

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        if bp.body:
            query.append_nl(
                "AS {body}",
                {
                    "body": bp.body,
                },
            )

        return query
