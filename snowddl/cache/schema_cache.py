from typing import TYPE_CHECKING

from snowddl.blueprint import Ident

if TYPE_CHECKING:
    from snowddl.engine import SnowDDLEngine


class SchemaCache:
    def __init__(self, engine: "SnowDDLEngine"):
        self.engine = engine

        self.databases = {}
        self.schemas = {}

        self.database_params = {}
        self.schema_params = {}

        self.reload()

    def reload(self):
        self.databases = {}
        self.schemas = {}

        cur = self.engine.execute_meta(
            "SHOW DATABASES LIKE {env_prefix:ls}",
            {
                "env_prefix": self.engine.config.env_prefix,
            },
        )

        for r in cur:
            # Skip databases created by other roles
            if r["owner"] != self.engine.context.current_role and not self.engine.settings.ignore_ownership:
                continue

            # Skip non-standard databases
            if r["kind"] != "STANDARD":
                continue

            # Skip databases not listed in settings explicitly
            if self.engine.settings.include_databases and Ident(r["name"]) not in self.engine.settings.include_databases:
                continue

            self.databases[r["name"]] = {
                "database": r["name"],
                "owner": r["owner"],
                "comment": r["comment"] if r["comment"] else None,
                "is_transient": "TRANSIENT" in r["options"],
                "retention_time": int(r["retention_time"]),
            }

        # Load schemas in parallel
        for database_schemas in self.engine.executor.map(self._get_database_schemas, self.databases.values()):
            self.schemas.update(database_schemas)

        # Load database parameters in parallel
        for database_params in self.engine.executor.map(self._get_database_params, self.databases.values()):
            self.database_params.update(database_params)

        # Load schema params parameters in parallel
        for schema_params in self.engine.executor.map(self._get_schema_params, self.schemas.values()):
            self.schema_params.update(schema_params)

    def _get_database_schemas(self, database_row):
        schemas = {}

        cur = self.engine.execute_meta(
            "SHOW SCHEMAS IN DATABASE {database:i}",
            {
                "database": database_row["database"],
            },
        )

        for r in cur:
            # Skip INFORMATION_SCHEMA
            if r["name"] == "INFORMATION_SCHEMA":
                continue

            schemas[f"{r['database_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["name"],
                "owner": r["owner"],
                "comment": r["comment"] if r["comment"] else None,
                "is_transient": "TRANSIENT" in r["options"],
                "is_managed_access": "MANAGED ACCESS" in r["options"],
                "retention_time": int(r["retention_time"]) if r["retention_time"].isdigit() else 0,
            }

        return schemas

    def _get_database_params(self, database_row):
        database_params = {database_row["database"]: {}}

        cur = self.engine.execute_meta(
            "SHOW PARAMETERS IN DATABASE {database:i}",
            {
                "database": database_row["database"],
            },
        )

        for r in cur:
            if r["level"] == "DATABASE":
                database_params[database_row["database"]][r["key"]] = r["value"]

        return database_params

    def _get_schema_params(self, schema_row):
        schema_name = f"{schema_row['database']}.{schema_row['schema']}"
        schema_params = {schema_name: {}}

        cur = self.engine.execute_meta(
            "SHOW PARAMETERS IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema_row["database"],
                "schema": schema_row["schema"],
            },
        )

        for r in cur:
            if r["level"] == "SCHEMA":
                schema_params[schema_name][r["key"]] = r["value"]

        return schema_params
