def test_step1(helper):
    database_params = helper.show_database_parameters("db1")

    assert database_params["EVENT_TABLE"]["level"] == "DATABASE"
    assert database_params["EVENT_TABLE"]["value"].endswith(".SC1.ET003_ET1")


def test_step2(helper):
    database_params = helper.show_database_parameters("db1")

    assert database_params["EVENT_TABLE"]["level"] == "DATABASE"
    assert database_params["EVENT_TABLE"]["value"].endswith(".SC1.ET003_ET2")


def test_step3(helper):
    database_params = helper.show_database_parameters("db1")

    assert database_params["EVENT_TABLE"]["level"] == ""
    assert database_params["EVENT_TABLE"]["value"] == database_params["EVENT_TABLE"]["default"]
