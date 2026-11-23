from unittest.mock import Mock, call

from snowddl.converter.view import ViewConverter
from snowddl.resolver._utils import SHOW_PAGE_SIZE, iter_show_rows
from snowddl.resolver.view import ViewResolver


def view_row(name, is_materialized="false"):
    return {
        "database_name": "DB1",
        "schema_name": "SC1",
        "name": name,
        "owner": "OWNER",
        "text": f"CREATE VIEW {name} AS SELECT 1",
        "is_secure": "false",
        "is_materialized": is_materialized,
        "comment": "",
    }


def test_step1_iter_show_rows_paginates_any_show_command():
    first_page = [{"name": f"TB_{index:05d}"} for index in range(SHOW_PAGE_SIZE)]
    second_page = [{"name": "TB_10000"}]
    engine = Mock()
    engine.execute_meta.side_effect = [first_page, second_page]

    rows = list(iter_show_rows(engine, "SHOW TABLES IN SCHEMA {schema:i}", {"schema": "SC1"}))

    assert len(rows) == SHOW_PAGE_SIZE + 1
    assert rows[-1]["name"] == "TB_10000"
    assert engine.execute_meta.call_args_list == [
        call(
            "SHOW TABLES IN SCHEMA {schema:i} LIMIT {__page_size:d}",
            {"schema": "SC1", "__page_size": SHOW_PAGE_SIZE},
        ),
        call(
            "SHOW TABLES IN SCHEMA {schema:i} LIMIT {__page_size:d} FROM {__from_name}",
            {"schema": "SC1", "__page_size": SHOW_PAGE_SIZE, "__from_name": f"TB_{SHOW_PAGE_SIZE - 1:05d}"},
        ),
    ]


def test_step1_iter_show_rows_stops_on_partial_page():
    engine = Mock()
    engine.execute_meta.side_effect = [[{"name": "TB_1"}]]

    rows = list(iter_show_rows(engine, "SHOW TABLES IN SCHEMA {schema:i}", {"schema": "SC1"}))

    assert len(rows) == 1
    assert engine.execute_meta.call_count == 1


def test_step1_iter_show_rows_requests_empty_page_after_exact_page_size():
    first_page = [{"name": f"TB_{index:05d}"} for index in range(SHOW_PAGE_SIZE)]
    engine = Mock()
    engine.execute_meta.side_effect = [first_page, []]

    rows = list(iter_show_rows(engine, "SHOW TABLES IN SCHEMA {schema:i}", {"schema": "SC1"}))

    assert len(rows) == SHOW_PAGE_SIZE
    assert engine.execute_meta.call_count == 2


def test_step1_converter_paginates_show_views():
    first_page = [view_row(f"VIEW_{index:05d}") for index in range(SHOW_PAGE_SIZE)]
    first_page[-1] = view_row("VIEW_09999", is_materialized="true")
    second_page = [view_row("VIEW_10000")]
    engine = Mock()
    engine.execute_meta.side_effect = [first_page, second_page]
    converter = object.__new__(ViewConverter)
    converter.engine = engine

    result = converter.get_existing_objects_in_schema({"database": "DB1", "schema": "SC1"})

    assert len(result) == SHOW_PAGE_SIZE
    assert "DB1.SC1.VIEW_09999" not in result
    assert result["DB1.SC1.VIEW_10000"]["name"] == "VIEW_10000"
    assert engine.execute_meta.call_args_list == [
        call(
            "SHOW VIEWS IN SCHEMA {database:i}.{schema:i} LIMIT {__page_size:d}",
            {"database": "DB1", "schema": "SC1", "__page_size": SHOW_PAGE_SIZE},
        ),
        call(
            "SHOW VIEWS IN SCHEMA {database:i}.{schema:i} LIMIT {__page_size:d} FROM {__from_name}",
            {
                "database": "DB1",
                "schema": "SC1",
                "__page_size": SHOW_PAGE_SIZE,
                "__from_name": "VIEW_09999",
            },
        ),
    ]


def test_step1_resolver_paginates_show_views():
    first_page = [view_row(f"VIEW_{index:05d}") for index in range(SHOW_PAGE_SIZE)]
    second_page = [view_row("VIEW_10000")]
    engine = Mock()
    engine.execute_meta.side_effect = [first_page, second_page]
    resolver = object.__new__(ViewResolver)
    resolver.engine = engine

    result = resolver.get_existing_objects_in_schema({"database": "DB1", "schema": "SC1"})

    assert len(result) == SHOW_PAGE_SIZE + 1
    assert result["DB1.SC1.VIEW_10000"]["name"] == "VIEW_10000"
