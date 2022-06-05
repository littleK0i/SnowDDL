from typing import TYPE_CHECKING

from snowddl.blueprint import Ident

if TYPE_CHECKING:
    from snowddl.engine import SnowDDLEngine


class SnowDDLSchemaCache:
    def __init__(self, engine: "SnowDDLEngine"):
        self.engine = engine

        self.databases = {}
        self.schemas = {}

        self.reload()

    def reload(self):
        self.databases = {}
        self.schemas = {}

        cur = self.engine.execute_meta("SHOW DATABASES LIKE {env_prefix:ls}", {
            'env_prefix': self.engine.config.env_prefix,
        })

        for r in cur:
            # Skip databases created by other roles
            if r['owner'] != self.engine.context.current_role and not self.engine.settings.ignore_ownership:
                continue

            # Skip shares
            if r['origin']:
                continue

            # Skip databases not listed in settings explicitly
            if self.engine.settings.include_databases \
            and Ident(r['name']) not in self.engine.settings.include_databases:
                continue

            self.databases[r['name']] = {
                "database": r['name'],
                "owner": r['owner'],
                "comment": r['comment'] if r['comment'] else None,
                "is_transient": "TRANSIENT" in r['options'],
                "retention_time": int(r['retention_time']),
            }

        # Process schemas in parallel
        for database_schemas in self.engine.executor.map(self._get_database_schemas, self.databases):
            self.schemas.update(database_schemas)

    def _get_database_schemas(self, database_name):
        schemas = {}

        cur = self.engine.execute_meta("SHOW SCHEMAS IN DATABASE {database:i}", {
            "database": database_name,
        })

        for r in cur:
            # Skip schemas created by other roles
            if r['owner'] != self.engine.context.current_role and not self.engine.settings.ignore_ownership:
                continue

            # Skip INFORMATION_SCHEMA
            if r['name'] == "INFORMATION_SCHEMA":
                continue

            schemas[f"{r['database_name']}.{r['name']}"] = {
                "database": r['database_name'],
                "schema": r['name'],
                "owner": r['owner'],
                "comment": r['comment'] if r['comment'] else None,
                "is_transient": "TRANSIENT" in r['options'],
                "is_managed_access": "MANAGED ACCESS" in r['options'],
                "retention_time": int(r['retention_time']) if r['retention_time'].isdigit() else 0,
            }

        return schemas
