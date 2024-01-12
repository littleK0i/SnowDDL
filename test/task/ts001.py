def test_step1(helper):
    show = helper.show_task("db1", "sc1", "ts001_ts1")

    assert str(show["warehouse"]).startswith(".TS001_WH1")
    assert show["schedule"] == "60 minutes"
    assert show["predecessors"] == "[]"
    assert show["state"] == "suspended"
    assert show["definition"] == "SELECT 1"
    assert show["condition"] is None
    assert show["allow_overlapping_execution"] == "false"
    assert show["error_integration"] == "null"  # ... Snowflake weirdness
    assert show["config"] is None

    assert str(show["comment"]).startswith("abc #")


def test_step2(helper):
    show = helper.show_task("db1", "sc1", "ts001_ts1")

    assert show["warehouse"] is None
    assert show["schedule"] == "USING CRON 0 0 10-20 * TUE,THU UTC"
    assert show["predecessors"] == "[]"
    assert show["state"] == "suspended"
    assert show["definition"] == "SELECT 1"
    assert show["condition"] is None
    assert show["allow_overlapping_execution"] == "false"
    assert show["error_integration"] == "TEST_NOTIFICATION_INTEGRATION"
    assert show["config"] == '{"foo": "bar"}'

    assert str(show["comment"]).startswith("cde #")


def test_step3(helper):
    show = helper.show_task("db1", "sc1", "ts001_ts1")

    assert show is None
