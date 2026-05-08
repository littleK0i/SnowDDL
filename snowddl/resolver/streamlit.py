from snowddl.blueprint import StreamlitBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType
from snowddl.resolver._utils import coalesce


class StreamlitResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.STREAMLIT

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW STREAMLITS IN SCHEMA {database:i}.{schema:i}",
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
                "title": r["title"] if r["title"] else None,
                "query_warehouse": r["query_warehouse"] if r["query_warehouse"] else None,
                "main_file": r["main_file"],
                "root_location": r["root_location"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(StreamlitBlueprint)

    def create_object(self, bp: StreamlitBlueprint):
        self.engine.execute_safe_ddl(self._build_create_streamlit(bp))
        return ResolveResult.CREATE

    def compare_object(self, bp: StreamlitBlueprint, row: dict):
        expected_root = self._build_root_location(bp)

        if expected_root != row["root_location"]:
            self.engine.execute_safe_ddl(self._build_create_streamlit(bp, replace=True))
            return ResolveResult.REPLACE

        result = ResolveResult.NOCHANGE
        alter_params = {}

        if bp.main_file != row["main_file"]:
            alter_params["main_file"] = bp.main_file

        if (bp.query_warehouse.name.upper() if bp.query_warehouse else None) != (row["query_warehouse"].upper() if row["query_warehouse"] else None):
            alter_params["query_warehouse"] = bp.query_warehouse

        if bp.title != row["title"]:
            alter_params["title"] = bp.title

        if bp.comment != row["comment"]:
            alter_params["comment"] = bp.comment

        if alter_params or bp.external_access_integrations is not None or bp.secrets is not None:
            self.engine.execute_safe_ddl(self._build_alter_streamlit(bp, alter_params))
            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP STREAMLIT {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_root_location(self, bp: StreamlitBlueprint) -> str:
        directory = coalesce(bp.stage_directory, "/")
        if not directory.startswith("/"):
            directory = f"/{directory}"
        if not directory.endswith("/"):
            directory = f"{directory}/"
        return f"@{bp.stage}/{directory}".rstrip("/")

    def _build_create_streamlit(self, bp: StreamlitBlueprint, replace: bool = False):
        query = self.engine.query_builder()

        if replace:
            query.append("CREATE OR REPLACE STREAMLIT {full_name:i}", {"full_name": bp.full_name})
        else:
            query.append("CREATE STREAMLIT {full_name:i}", {"full_name": bp.full_name})

        directory = coalesce(bp.stage_directory, "")
        if directory and not directory.startswith("/"):
            directory = f"/{directory}"

        query.append_nl(
            "FROM '@{stage_name:i}{directory:r}'",
            {
                "stage_name": bp.stage,
                "directory": directory,
            },
        )

        query.append_nl(
            "MAIN_FILE = {main_file}",
            {
                "main_file": bp.main_file,
            },
        )

        if bp.query_warehouse:
            query.append_nl(
                "QUERY_WAREHOUSE = {query_warehouse:i}",
                {
                    "query_warehouse": bp.query_warehouse,
                },
            )

        if bp.title:
            query.append_nl(
                "TITLE = {title}",
                {
                    "title": bp.title,
                },
            )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        if bp.external_access_integrations:
            query.append_nl("EXTERNAL_ACCESS_INTEGRATIONS = (")

            for idx, integration in enumerate(bp.external_access_integrations):
                query.append_nl(
                    "    {comma:r}{integration:i}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "integration": integration,
                    },
                )

            query.append_nl(")")

        if bp.secrets:
            query.append_nl("SECRETS = (")

            for idx, (secret_key, secret_name) in enumerate(bp.secrets.items()):
                query.append_nl(
                    "    {comma:r}{secret_key} = {secret_name:i}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "secret_key": secret_key,
                        "secret_name": secret_name,
                    },
                )

            query.append_nl(")")

        return query

    def _build_alter_streamlit(self, bp: StreamlitBlueprint, alter_params: dict):
        query = self.engine.query_builder()

        query.append("ALTER STREAMLIT {full_name:i} SET", {"full_name": bp.full_name})

        if "main_file" in alter_params:
            query.append_nl(
                "MAIN_FILE = {main_file}",
                {
                    "main_file": alter_params["main_file"],
                },
            )

        if "query_warehouse" in alter_params:
            if alter_params["query_warehouse"]:
                query.append_nl(
                    "QUERY_WAREHOUSE = {query_warehouse:i}",
                    {
                        "query_warehouse": alter_params["query_warehouse"],
                    },
                )
            else:
                query.append_nl("QUERY_WAREHOUSE = NULL")

        if "title" in alter_params:
            if alter_params["title"]:
                query.append_nl(
                    "TITLE = {title}",
                    {
                        "title": alter_params["title"],
                    },
                )
            else:
                query.append_nl("TITLE = NULL")

        if "comment" in alter_params:
            if alter_params["comment"]:
                query.append_nl(
                    "COMMENT = {comment}",
                    {
                        "comment": alter_params["comment"],
                    },
                )
            else:
                query.append_nl("COMMENT = NULL")

        if bp.external_access_integrations is not None:
            query.append_nl("EXTERNAL_ACCESS_INTEGRATIONS = (")

            for idx, integration in enumerate(bp.external_access_integrations):
                query.append_nl(
                    "    {comma:r}{integration:i}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "integration": integration,
                    },
                )

            query.append_nl(")")

        if bp.secrets is not None:
            query.append_nl("SECRETS = (")

            for idx, (secret_key, secret_name) in enumerate(bp.secrets.items()):
                query.append_nl(
                    "    {comma:r}{secret_key} = {secret_name:i}",
                    {
                        "comma": "  " if idx == 0 else ", ",
                        "secret_key": secret_key,
                        "secret_name": secret_name,
                    },
                )

            query.append_nl(")")

        return query
