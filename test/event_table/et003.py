def test_step1(helper):
    event_table_param = helper.show_database_parameters("db1")["EVENT_TABLE"]

    assert event_table_param["value"] == f"{helper.env_prefix}DB1.SC1.ET001_ET1"
    assert event_table_param["level"] == "DATABASE"


def test_step2(helper):
    event_table_param = helper.show_database_parameters("db1")["EVENT_TABLE"]

    assert event_table_param["value"] == f"{helper.env_prefix}DB1.SC1.ET002_ET1"
    assert event_table_param["level"] == "DATABASE"


def test_step3(helper):
    event_table_param = helper.show_database_parameters("db1")["EVENT_TABLE"]

    assert event_table_param["level"] != "DATABASE"
