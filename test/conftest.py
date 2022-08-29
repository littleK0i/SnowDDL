from json import loads
from itertools import groupby
from os import environ
from pytest import fixture
from snowflake.connector import connect, DictCursor

from snowddl import (
    Edition,
    Ident,
    AccountObjectIdent,
    SchemaIdent,
    SchemaObjectIdent,
    SnowDDLFormatter,
    SnowDDLQueryBuilder,
)


class Helper:
    DEFAULT_ENV_PREFIX = 'PYTEST'

    def __init__(self):
        self.connection = self._init_connection()
        self.env_prefix = self._init_env_prefix()
        self.formatter = SnowDDLFormatter()

        self.edition = self._init_edition()

    def execute(self, sql, params=None):
        sql = self.formatter.format_sql(sql, params)

        return self.connection.cursor(DictCursor).execute(sql)

    def query_builder(self):
        return SnowDDLQueryBuilder(self.formatter)

    def desc_table(self, database, schema, name):
        cur = self.execute("DESC TABLE {table_name:i}", {
            "table_name": SchemaObjectIdent(self.env_prefix, database, schema, name)
        })

        return {r['name']: r for r in cur}

    def desc_view(self, database, schema, name):
        cur = self.execute("DESC VIEW {table_name:i}", {
            "table_name": SchemaObjectIdent(self.env_prefix, database, schema, name)
        })

        return {r['name']: r for r in cur}

    def show_sequence(self, database, schema, name):
        cur = self.execute("SHOW SEQUENCES LIKE {sequence_name:lf} IN SCHEMA {schema_name:i}", {
            "schema_name": SchemaIdent(self.env_prefix, database, schema),
            "sequence_name": Ident(name),
        })

        return cur.fetchone()

    def show_table(self, database, schema, name):
        cur = self.execute("SHOW TABLES LIKE {table_name:lf} IN SCHEMA {schema_name:i}", {
            "schema_name": SchemaIdent(self.env_prefix, database, schema),
            "table_name": Ident(name),
        })

        return cur.fetchone()

    def show_user(self, name):
        cur = self.execute("SHOW USERS LIKE {user_name:lf}", {
            "user_name": AccountObjectIdent(self.env_prefix, name),
        })

        return cur.fetchone()

    def show_view(self, database, schema, name):
        cur = self.execute("SHOW VIEWS LIKE {view_name:lf} IN SCHEMA {schema_name:i}", {
            "schema_name": SchemaIdent(self.env_prefix, database, schema),
            "view_name": Ident(name),
        })

        return cur.fetchone()

    def show_primary_key(self, database, schema, name):
        cur = self.execute("SHOW PRIMARY KEYS IN TABLE {table_name:i}", {
            "table_name": SchemaObjectIdent(self.env_prefix, database, schema, name)
        })

        sorted_cur = sorted(cur, key=lambda r: r['key_sequence'])

        return [r['column_name'] for r in sorted_cur]

    def show_unique_keys(self, database, schema, name):
        cur = self.execute("SHOW UNIQUE KEYS IN TABLE {table_name:i}", {
            "table_name": SchemaObjectIdent(self.env_prefix, database, schema, name)
        })

        sorted_cur = sorted(cur, key=lambda r: (r['constraint_name'], r['key_sequence']))

        return [[r['column_name'] for r in g] for k, g in groupby(sorted_cur, lambda r: r['constraint_name'])]

    def show_foreign_keys(self, database, schema, name):
        cur = self.execute("SHOW IMPORTED KEYS IN TABLE {table_name:i}", {
            "table_name": SchemaObjectIdent(self.env_prefix, database, schema, name)
        })

        sorted_cur = sorted(cur, key=lambda r: (r['fk_name'], r['key_sequence']))
        fk = []

        for k, g in groupby(sorted_cur, lambda r: r['fk_name']):
            g = list(g)

            fk.append({
                "columns": [r['fk_column_name'] for r in g],
                "ref_table": f"{g[0]['pk_database_name']}.{g[0]['pk_schema_name']}.{g[0]['pk_table_name']}",
                "ref_columns": [r['pk_column_name'] for r in g],
            })

        return fk

    def is_edition_enterprise(self):
        return self.edition >= Edition.ENTERPRISE

    def is_edition_business_critical(self):
        return self.edition >= Edition.BUSINESS_CRITICAL

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

    def _init_connection(self):
        options = {
            "account": environ.get('SNOWFLAKE_ACCOUNT'),
            "user": environ.get('SNOWFLAKE_USER'),
            "password": environ.get('SNOWFLAKE_PASSWORD'),
        }

        return connect(**options)

    def _init_env_prefix(self):
        return environ.get("SNOWFLAKE_ENV_PREFIX", self.DEFAULT_ENV_PREFIX).upper() + "__"

    def _init_edition(self):
        cur = self.execute("SELECT SYSTEM$BOOTSTRAP_DATA_REQUEST('ACCOUNT') AS bootstrap_account")
        r = cur.fetchone()

        bootstrap_account = loads(r['BOOTSTRAP_ACCOUNT'])

        return Edition[bootstrap_account['accountInfo']['serviceLevelName']]

@fixture(scope="session")
def helper():
    with Helper() as helper:
        yield helper
