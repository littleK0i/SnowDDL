def test_step1(helper):
    show = helper.show_task("db1", "sc1", "ts003_ts1")
    show_params = helper.show_task_parameters("db1", "sc1", "ts003_ts1")

    # Parameter is in private preview
    # assert show["scheduling_mode"] == "FLEXIBLE"

    assert show["warehouse"] is None
    assert show["schedule"] == "6 hours"
    assert show["target_completion_interval"] == "2 hours"

    assert show["error_integration"] == "TEST_NOTIFICATION_INTEGRATION"
    assert show["success_integration"] == "TEST_NOTIFICATION_INTEGRATION"

    assert show_params["LOG_LEVEL"]["value"] == "INFO"
    assert show_params["SERVERLESS_TASK_MIN_STATEMENT_SIZE"]["value"] == "XSMALL"
    assert show_params["SERVERLESS_TASK_MAX_STATEMENT_SIZE"]["value"] == "SMALL"
    assert show_params["USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE"]["value"] == "XSMALL"
    assert show_params["USER_TASK_MINIMUM_TRIGGER_INTERVAL_IN_SECONDS"]["value"] == "30"


def test_step2(helper):
    show = helper.show_task("db1", "sc1", "ts003_ts1")
    show_params = helper.show_task_parameters("db1", "sc1", "ts003_ts1")

    # Parameter is in private preview
    # assert show["scheduling_mode"] == "FIXED"

    assert show["warehouse"] is None
    assert show["schedule"] == "6 hours"
    assert show["target_completion_interval"] == "3 hours"

    assert show["error_integration"] == "null"
    assert show["success_integration"] == "null"

    assert show_params["LOG_LEVEL"]["value"] == "ERROR"
    assert show_params["SERVERLESS_TASK_MIN_STATEMENT_SIZE"]["value"] == "SMALL"
    assert show_params["SERVERLESS_TASK_MAX_STATEMENT_SIZE"]["value"] == "MEDIUM"
    assert show_params["USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE"]["value"] == "SMALL"
    assert show_params["USER_TASK_MINIMUM_TRIGGER_INTERVAL_IN_SECONDS"]["value"] == "60"


def test_step3(helper):
    show = helper.show_task("db1", "sc1", "ts003_ts1")

    assert show is None
