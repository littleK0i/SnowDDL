from abc import ABC
from pytest import fixture
from os import environ
from snowflake.connector import connect

from snowddl import *


class AbstractTest(ABC):
    test_db = "TEST_DB"
    test_sc = "TEST_SC"
    test_table = "TEST_TABLE"

    @fixture
    def env_prefix(self, worker_id):
        return f"PYTEST_{worker_id}"

    @fixture
    def connection(self):
        options = {
            "account": environ.get('SNOWFLAKE_ACCOUNT'),
            "user": environ.get('SNOWFLAKE_USER'),
            "password": environ.get('SNOWFLAKE_PASSWORD'),
        }

        with connect(**options) as connection:
            yield connection

    @fixture
    def config(self, env_prefix):
        config = SnowDDLConfig(env_prefix)

        config.add_blueprint(self.base_database_bp(config, self.test_db))
        config.add_blueprint(self.base_schema_bp(config, self.test_db, self.test_sc))
        config.add_blueprint(self.base_table_bp(config, self.test_db, self.test_sc, self.test_table))

        yield config

    @fixture
    def settings(self):
        settings = SnowDDLSettings()
        settings.execute_safe_ddl = True
        settings.execute_unsafe_ddl = True

        return settings

    @fixture
    def engine(self, connection, config, settings):
        engine = SnowDDLEngine(connection, config, settings)

        with engine:
            # Cleanup objects from previous test run
            self.destroy_objects(engine)

            # Build base environment
            self.resolve_objects(engine)

            # Cleanup logs
            engine.executed_ddl = []
            engine.suggested_ddl = []

            yield engine

    def get_resolver_sequence(self):
        return [
            DatabaseResolver,
            SchemaResolver,
            TableResolver,
        ]

    def resolve_objects(self, engine: SnowDDLEngine):
        for resolver_cls in self.get_resolver_sequence():
            resolver = resolver_cls(engine)
            resolver.resolve()

            for error in resolver.errors.values():
                raise error

    def destroy_objects(self, engine: SnowDDLEngine):
        for resolver_cls in self.get_resolver_sequence():
            resolver = resolver_cls(engine)
            resolver.destroy()

            for error in resolver.errors.values():
                raise error

    def base_database_bp(self, config: SnowDDLConfig, database_name):
        return DatabaseBlueprint(
            full_name=DatabaseIdent(config.env_prefix, database_name),
            is_transient=True,
            retention_time=None,
            is_sandbox=False,
            comment=None,
        )

    def base_schema_bp(self, config: SnowDDLConfig, database_name, schema_name):
        return SchemaBlueprint(
            full_name=SchemaIdent(config.env_prefix, database_name, schema_name),
            is_transient=True,
            retention_time=None,
            is_sandbox=False,
            owner_additional_grants=[],
            comment=None,
        )

    def base_table_bp(self, config: SnowDDLConfig, database_name, schema_name, table_name):
        base_cols = {
            "num1": "NUMBER(10,0)",
            "num2": "NUMBER(38,0)",
            "num3": "NUMBER(10,5)",
            "num4": "NUMBER(38,37)",
            "dbl": "FLOAT",
            "bin1": "BINARY(10)",
            "bin2": "BINARY(8388608)",
            "var1": "VARCHAR(10)",
            "var2": "VARCHAR(16777216)",
            "dt1": "DATE",
            "tm1": "TIME(0)",
            "tm2": "TIME(9)",
            "ltz1": "TIMESTAMP_LTZ(0)",
            "ltz2": "TIMESTAMP_LTZ(9)",
            "ntz1": "TIMESTAMP_NTZ(0)",
            "ntz2": "TIMESTAMP_NTZ(9)",
            "tz1": "TIMESTAMP_TZ(0)",
            "tz2": "TIMESTAMP_TZ(9)",
            "var": "VARIANT",
            "obj": "OBJECT",
            "arr": "ARRAY",
            "geo": "GEOGRAPHY",
        }

        col_blueprints = []

        for col_name, col_type in base_cols.items():
            col_blueprints.append(
                TableColumn(
                    name=Ident(col_name),
                    type=DataType(col_type),
                    not_null=False,
                    default=None,
                    comment=None,
                )
            )

        return TableBlueprint(
            full_name=SchemaObjectIdent(config.env_prefix, database_name, schema_name, table_name),
            columns=col_blueprints,
            cluster_by=None,
            is_transient=True,
            retention_time=None,
            change_tracking=False,
            search_optimization=False,
            comment=None,
        )
