from json import loads
from itertools import groupby
from os import environ
from pytest import fixture
from snowflake.connector import connect, DictCursor

from snowddl import (
    BaseDataType,
    Edition,
    Ident,
    AccountObjectIdent,
    SchemaIdent,
    SchemaObjectIdent,
    SchemaObjectIdentWithArgs,
    SnowDDLFormatter,
    SnowDDLQueryBuilder,
)
from snowflake.connector.cursor import SnowflakeCursor


class Helper:
    DEFAULT_ENV_PREFIX = 'PYTEST'

    def __init__(self):
        self.connection = self._init_connection()
        self.env_prefix = self._init_env_prefix()
        self.formatter = SnowDDLFormatter()

        self.edition = self._init_edition()

        self._activate_role_with_prefix()

    def execute(self, sql, params=None) -> SnowflakeCursor:
        sql = self.formatter.format_sql(sql, params)

        return self.connection.cursor(DictCursor).execute(sql)

    def query_builder(self):
        return SnowDDLQueryBuilder(self.formatter)

    def desc_search_optimization(self, database, schema, name):
        cur = self.execute("DESC SEARCH OPTIMIZATION ON {table_name:i}", {
            "table_name": SchemaObjectIdent(self.env_prefix, database, schema, name)
        })

        items = []

        for r in cur:
            items.append({
                "method": r['method'],
                "target": r['target'],
            })

        return items

    def desc_table(self, database, schema, name):
        cur = self.execute("DESC TABLE {name:i}", {
            "name": SchemaObjectIdent(self.env_prefix, database, schema, name)
        })

        return {r['name']: r for r in cur}

    def desc_view(self, database, schema, name):
        cur = self.execute("DESC VIEW {name:i}", {
            "name": SchemaObjectIdent(self.env_prefix, database, schema, name)
        })

        return {r['name']: r for r in cur}

    def desc_function(self, database, schema, name, dtypes):
        cur = self.execute("DESC FUNCTION {name:i}", {
            "name": SchemaObjectIdentWithArgs(self.env_prefix, database, schema, name, dtypes)
        })

        return {r['property']: r['value'] for r in cur}

    def desc_procedure(self, database, schema, name, dtypes):
        cur = self.execute("DESC PROCEDURE {name:i}", {
            "name": SchemaObjectIdentWithArgs(self.env_prefix, database, schema, name, dtypes)
        })

        return {r['property']: r['value'] for r in cur}

    def desc_file_format(self, database, schema, name):
        cur = self.execute("DESC FILE FORMAT {name:i}", {
            "name": SchemaObjectIdent(self.env_prefix, database, schema, name)
        })

        return {r['property']: r for r in cur}

    def desc_network_policy(self, name):
        cur = self.execute("DESC NETWORK POLICY {name:i}", {
            "name": AccountObjectIdent(self.env_prefix, name)
        })

        return {r['name']: r for r in cur}

    def desc_stage(self, database, schema, name):
        cur = self.execute("DESC STAGE {name:i}", {
            "name": SchemaObjectIdent(self.env_prefix, database, schema, name)
        })

        result = {}

        for r in cur:
            if r['parent_property'] not in result:
                result[r['parent_property']] = {}

            result[r['parent_property']][r['property']] = r

        return result

    def show_alert(self, database, schema, name):
        cur = self.execute("SHOW ALERTS LIKE {alert_name:lf} IN SCHEMA {schema_name:i}", {
            "schema_name": SchemaIdent(self.env_prefix, database, schema),
            "alert_name": Ident(name),
        })

        return cur.fetchone()

    def show_dynamic_table(self, database, schema, name):
        cur = self.execute("SHOW DYNAMIC TABLES LIKE {table_name:lf} IN SCHEMA {schema_name:i}", {
            "schema_name": SchemaIdent(self.env_prefix, database, schema),
            "table_name": Ident(name),
        })

        return cur.fetchone()

    def show_sequence(self, database, schema, name):
        cur = self.execute("SHOW SEQUENCES LIKE {sequence_name:lf} IN SCHEMA {schema_name:i}", {
            "schema_name": SchemaIdent(self.env_prefix, database, schema),
            "sequence_name": Ident(name),
        })

        return cur.fetchone()

    def show_stage(self, database, schema, name):
        cur = self.execute("SHOW STAGES LIKE {stage_name:lf} IN SCHEMA {schema_name:i}", {
            "schema_name": SchemaIdent(self.env_prefix, database, schema),
            "stage_name": Ident(name),
        })

        return cur.fetchone()

    def show_table(self, database, schema, name):
        cur = self.execute("SHOW TABLES LIKE {table_name:lf} IN SCHEMA {schema_name:i}", {
            "schema_name": SchemaIdent(self.env_prefix, database, schema),
            "table_name": Ident(name),
        })

        return cur.fetchone()

    def show_function(self, database, schema, name):
        cur = self.execute("SHOW USER FUNCTIONS LIKE {function_name:lf} IN SCHEMA {schema_name:i}", {
            "schema_name": SchemaIdent(self.env_prefix, database, schema),
            "function_name": Ident(name),
        })

        return cur.fetchone()

    def show_procedure(self, database, schema, name):
        cur = self.execute("SHOW USER PROCEDURES LIKE {procedure_name:lf} IN SCHEMA {schema_name:i}", {
            "schema_name": SchemaIdent(self.env_prefix, database, schema),
            "procedure_name": Ident(name),
        })

        return cur.fetchone()

    def show_file_format(self, database, schema, name):
        cur = self.execute("SHOW FILE FORMATS LIKE {format_name:lf} IN SCHEMA {schema_name:i}", {
            "schema_name": SchemaIdent(self.env_prefix, database, schema),
            "format_name": Ident(name),
        })

        return cur.fetchone()

    def show_user(self, name):
        cur = self.execute("SHOW USERS LIKE {user_name:lf}", {
            "user_name": AccountObjectIdent(self.env_prefix, name),
        })

        return cur.fetchone()

    def show_user_parameters(self, name):
        cur = self.execute("SHOW PARAMETERS IN USER {name:i}", {
            "name": AccountObjectIdent(self.env_prefix, name),
        })

        return {r['key']: r for r in cur}

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

    def show_network_policy(self, name):
        # SHOW NETWORK POLICIES does not support LIKE natively
        cur = self.execute("SHOW NETWORK POLICIES")

        for r in cur:
            if r['name'] == str(AccountObjectIdent(self.env_prefix, name)):
                return r

        return None

    def show_resource_monitor(self, name):
        cur = self.execute("SHOW RESOURCE MONITORS LIKE {name:lf}", {
            "name": AccountObjectIdent(self.env_prefix, name),
        })

        return cur.fetchone()

    def show_warehouse(self, name):
        cur = self.execute("SHOW WAREHOUSES LIKE {name:lf}", {
            "name": AccountObjectIdent(self.env_prefix, name),
        })

        return cur.fetchone()

    def show_warehouse_parameters(self, name):
        cur = self.execute("SHOW PARAMETERS IN WAREHOUSE {name:i}", {
            "name": AccountObjectIdent(self.env_prefix, name),
        })

        return {r['key']: r for r in cur}

    def is_edition_enterprise(self):
        return self.edition >= Edition.ENTERPRISE

    def is_edition_business_critical(self):
        return self.edition >= Edition.BUSINESS_CRITICAL

    def dtypes_from_arguments(self, arguments):
        start_dtypes_idx = arguments.index('(')
        finish_dtypes_idx = arguments.index(')')

        if finish_dtypes_idx - start_dtypes_idx == 1:
            return []

        return [BaseDataType[a.strip(' ')] for a in arguments[start_dtypes_idx+1:finish_dtypes_idx].split(',')]

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

    def _activate_role_with_prefix(self):
        if not self.env_prefix:
            return

        cur = self.execute("SELECT CURRENT_ROLE() AS current_role")
        r = cur.fetchone()

        self.execute("USE ROLE {role_with_prefix:i}", {
            "role_with_prefix": AccountObjectIdent(self.env_prefix, r['CURRENT_ROLE']),
        })

@fixture(scope="session")
def helper():
    with Helper() as helper:
        yield helper
