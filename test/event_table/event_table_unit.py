import pytest

from snowddl import SnowDDLConfig, SnowDDLFormatter
from snowddl.blueprint import AccountParameterBlueprint, DatabaseBlueprint, DatabaseIdent, SchemaObjectIdent
from snowddl.parser import AccountParameterParser, DatabaseParser
from snowddl.parser._scanner import DirectoryScanner
from snowddl.resolver import EventTableResolver
from snowddl.settings import SnowDDLSettings


class DummyEngine:
    def __init__(self, meta_rows=None, execute_account_params=True, is_account_admin=True):
        self.config = SnowDDLConfig(env_prefix="PYTEST__")
        self.settings = SnowDDLSettings(
            execute_safe_ddl=True,
            execute_unsafe_ddl=True,
            execute_account_params=execute_account_params,
        )
        self.context = DummyContext(is_account_admin=is_account_admin)
        self.formatter = SnowDDLFormatter()
        self.executed_sql = []
        self.suggested_sql = []
        self.meta_rows = meta_rows or {}

    def execute_unsafe_ddl(self, sql, params=None, condition=True, file_stream=None):
        if condition:
            self.executed_sql.append(self.formatter.format_sql(sql, params))
        else:
            self.suggested_sql.append(self.formatter.format_sql(sql, params))

    def execute_meta(self, sql, params=None):
        return DummyCursor(self.meta_rows.get(self.formatter.format_sql(sql, params), []))


class DummyCursor:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        if self.rows:
            return self.rows[0]

        return None


class DummyContext:
    def __init__(self, is_account_admin=True):
        self.is_account_admin = is_account_admin


def test_account_params_parser_stores_event_table_on_config(tmp_path):
    (tmp_path / "account_params.yaml").write_text("timezone: UTC\nevent_table: db1.sc1.et1\n", encoding="utf-8")

    config = SnowDDLConfig(env_prefix="PYTEST__")
    parser = AccountParameterParser(config, DirectoryScanner(tmp_path))

    parser.load_blueprints()

    account_params = config.get_blueprints_by_type(AccountParameterBlueprint)

    assert "TIMEZONE" in account_params
    assert "EVENT_TABLE" not in account_params
    assert str(config.account_event_table) == "PYTEST__DB1.SC1.ET1"


def test_account_params_parser_rejects_non_fully_qualified_event_table(tmp_path):
    (tmp_path / "account_params.yaml").write_text("event_table: sc1.et1\n", encoding="utf-8")

    config = SnowDDLConfig(env_prefix="PYTEST__")
    parser = AccountParameterParser(config, DirectoryScanner(tmp_path))

    parser.load_blueprints()

    assert len(parser.errors) == 1
    assert "database.schema.event_table" in str(next(iter(parser.errors.values())))


def test_database_parser_rejects_single_part_event_table_name(tmp_path):
    db_dir = tmp_path / "db1"
    db_dir.mkdir()
    (db_dir / "params.yaml").write_text("event_table: et1\n", encoding="utf-8")

    config = SnowDDLConfig(env_prefix="PYTEST__")
    parser = DatabaseParser(config, DirectoryScanner(tmp_path))

    with pytest.raises(ValueError, match="schema.event_table"):
        parser.load_blueprints()


def test_event_table_resolver_sets_desired_account_association():
    engine = DummyEngine(
        meta_rows={
            "SHOW PARAMETERS LIKE 'EVENT_TABLE' FOR ACCOUNT": [
                {"key": "EVENT_TABLE", "value": "SNOWFLAKE.TELEMETRY.EVENTS", "level": ""}
            ]
        },
        execute_account_params=True,
    )
    engine.config.account_event_table = SchemaObjectIdent("PYTEST__", "DB1", "SC1", "ET1")

    resolver = EventTableResolver(engine)
    resolver._post_process()

    assert engine.executed_sql == ['ALTER ACCOUNT SET EVENT_TABLE = "PYTEST__DB1"."SC1"."ET1"']


def test_event_table_resolver_destroy_mode_unsets_but_does_not_reset_account_association():
    engine = DummyEngine(
        meta_rows={
            "SHOW PARAMETERS LIKE 'EVENT_TABLE' FOR ACCOUNT": [
                {"key": "EVENT_TABLE", "value": "PYTEST__DB1.SC1.ET1", "level": "ACCOUNT"}
            ]
        },
        execute_account_params=True,
    )
    engine.config.account_event_table = SchemaObjectIdent("PYTEST__", "DB1", "SC1", "ET1")

    resolver = EventTableResolver(engine)
    resolver._is_destroy_mode = True

    resolver._pre_process()
    resolver._post_process()

    assert engine.executed_sql == ['ALTER ACCOUNT UNSET EVENT_TABLE']


def test_event_table_resolver_suggests_database_association_when_session_lacks_accountadmin():
    engine = DummyEngine(
        meta_rows={
            "SHOW PARAMETERS LIKE 'EVENT_TABLE' FOR ACCOUNT": [],
            "SHOW PARAMETERS LIKE 'EVENT_TABLE' IN DATABASE PYTEST__DB1": [
                {"key": "EVENT_TABLE", "value": "SNOWFLAKE.TELEMETRY.EVENTS", "level": ""}
            ],
        },
        is_account_admin=False,
    )
    engine.config.add_blueprint(
        DatabaseBlueprint(
            full_name=DatabaseIdent("PYTEST__", "DB1"),
            event_table=SchemaObjectIdent("PYTEST__", "DB1", "SC1", "ET1"),
        )
    )

    resolver = EventTableResolver(engine)
    resolver._post_process()

    assert engine.executed_sql == []
    assert engine.suggested_sql == ['ALTER DATABASE "PYTEST__DB1" SET EVENT_TABLE = "PYTEST__DB1"."SC1"."ET1"']
