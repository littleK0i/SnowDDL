def test_step1(helper):
    sc = helper.show_schema("db1", "sc1")
    sc_params = helper.show_schema_parameters("db1", "sc1")

    assert int(sc["retention_time"]) == 1
    assert sc["comment"] == "abc"

    assert sc_params["LOG_LEVEL"]["level"] == "SCHEMA"
    assert sc_params["LOG_LEVEL"]["value"] == "INFO"

    assert sc_params["LOG_EVENT_LEVEL"]["level"] == "SCHEMA"
    assert sc_params["LOG_EVENT_LEVEL"]["value"] == "WARN"

    assert sc_params["METRIC_LEVEL"]["level"] == "SCHEMA"
    assert sc_params["METRIC_LEVEL"]["value"] == "ALL"

    assert sc_params["TRACE_LEVEL"]["level"] == "SCHEMA"
    assert sc_params["TRACE_LEVEL"]["value"] == "ON_EVENT"

    assert sc_params["QUOTED_IDENTIFIERS_IGNORE_CASE"]["level"] == "SCHEMA"
    assert sc_params["QUOTED_IDENTIFIERS_IGNORE_CASE"]["value"] == "true"


def test_step2(helper):
    sc = helper.show_schema("db1", "sc1")
    sc_params = helper.show_schema_parameters("db1", "sc1")

    assert int(sc["retention_time"]) == 2
    assert sc["comment"] == "cde"

    assert sc_params["LOG_LEVEL"]["level"] == "SCHEMA"
    assert sc_params["LOG_LEVEL"]["value"] == "OFF"

    assert sc_params["LOG_EVENT_LEVEL"]["level"] == "SCHEMA"
    assert sc_params["LOG_EVENT_LEVEL"]["value"] == "OFF"

    assert sc_params["METRIC_LEVEL"]["level"] == "SCHEMA"
    assert sc_params["METRIC_LEVEL"]["value"] == "NONE"

    assert sc_params["TRACE_LEVEL"]["level"] == "SCHEMA"
    assert sc_params["TRACE_LEVEL"]["value"] == "OFF"

    assert sc_params["QUOTED_IDENTIFIERS_IGNORE_CASE"]["level"] == "SCHEMA"
    assert sc_params["QUOTED_IDENTIFIERS_IGNORE_CASE"]["value"] == "false"


def test_step3(helper):
    sc = helper.show_schema("db1", "sc1")
    sc_params = helper.show_schema_parameters("db1", "sc1")

    assert int(sc["retention_time"]) == 2  # not unset, persists from step2
    assert not sc["comment"]

    assert sc_params["LOG_LEVEL"]["level"] != "SCHEMA"
    assert sc_params["LOG_EVENT_LEVEL"]["level"] != "SCHEMA"
    assert sc_params["METRIC_LEVEL"]["level"] != "SCHEMA"
    assert sc_params["TRACE_LEVEL"]["level"] != "SCHEMA"
    assert sc_params["QUOTED_IDENTIFIERS_IGNORE_CASE"]["level"] != "SCHEMA"
