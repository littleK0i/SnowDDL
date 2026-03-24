def test_step1(helper):
    db = helper.show_database("db1")
    db_params = helper.show_database_parameters("db1")

    assert int(db["retention_time"]) == 5
    assert db["comment"] == "abc"

    assert db_params["LOG_LEVEL"]["level"] == "DATABASE"
    assert db_params["LOG_LEVEL"]["value"] == "DEBUG"

    assert db_params["LOG_EVENT_LEVEL"]["level"] == "DATABASE"
    assert db_params["LOG_EVENT_LEVEL"]["value"] == "WARN"

    assert db_params["METRIC_LEVEL"]["level"] == "DATABASE"
    assert db_params["METRIC_LEVEL"]["value"] == "ALL"

    assert db_params["TRACE_LEVEL"]["level"] == "DATABASE"
    assert db_params["TRACE_LEVEL"]["value"] == "ALWAYS"

    assert db_params["QUOTED_IDENTIFIERS_IGNORE_CASE"]["level"] == "DATABASE"
    assert db_params["QUOTED_IDENTIFIERS_IGNORE_CASE"]["value"] == "true"


def test_step2(helper):
    db = helper.show_database("db1")
    db_params = helper.show_database_parameters("db1")

    assert int(db["retention_time"]) == 7
    assert not db["comment"]

    assert db_params["LOG_LEVEL"]["level"] == "DATABASE"
    assert db_params["LOG_LEVEL"]["value"] == "INFO"

    assert db_params["LOG_EVENT_LEVEL"]["level"] == "DATABASE"
    assert db_params["LOG_EVENT_LEVEL"]["value"] == "ERROR"

    assert db_params["METRIC_LEVEL"]["level"] == "DATABASE"
    assert db_params["METRIC_LEVEL"]["value"] == "NONE"

    assert db_params["TRACE_LEVEL"]["level"] != "DATABASE"

    assert db_params["QUOTED_IDENTIFIERS_IGNORE_CASE"]["level"] == "DATABASE"
    assert db_params["QUOTED_IDENTIFIERS_IGNORE_CASE"]["value"] == "false"


def test_step3(helper):
    db = helper.show_database("db1")
    db_params = helper.show_database_parameters("db1")

    assert int(db["retention_time"]) == 7  # not unset, persists from step2
    assert not db["comment"]

    assert db_params["LOG_LEVEL"]["level"] != "DATABASE"
    assert db_params["LOG_EVENT_LEVEL"]["level"] != "DATABASE"
    assert db_params["METRIC_LEVEL"]["level"] != "DATABASE"
    assert db_params["TRACE_LEVEL"]["level"] != "DATABASE"
    assert db_params["QUOTED_IDENTIFIERS_IGNORE_CASE"]["level"] != "DATABASE"
