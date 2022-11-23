def test_step1(helper):
    wh = helper.show_warehouse("wh001_wh1")
    wh_params = helper.show_warehouse_parameters("wh001_wh1")

    assert wh['size'] == "X-Small"
    assert wh['type'] == "STANDARD"
    assert wh['min_cluster_count'] == 2
    assert wh['max_cluster_count'] == 4
    assert wh['scaling_policy'] == "STANDARD"
    assert wh['auto_suspend'] == 120
    assert wh['enable_query_acceleration'] == "true"
    assert wh['query_acceleration_max_scale_factor'] == 6
    assert wh['comment'] == "abc"

    assert wh_params['MAX_CONCURRENCY_LEVEL']['value'] == "2"
    assert wh_params['MAX_CONCURRENCY_LEVEL']['level'] == "WAREHOUSE"

    assert wh_params['STATEMENT_TIMEOUT_IN_SECONDS']['value'] == "100"
    assert wh_params['STATEMENT_TIMEOUT_IN_SECONDS']['level'] == "WAREHOUSE"


def test_step2(helper):
    wh = helper.show_warehouse("wh001_wh1")
    wh_params = helper.show_warehouse_parameters("wh001_wh1")

    assert wh['size'] == "Small"
    assert wh['type'] == "STANDARD"
    assert wh['min_cluster_count'] == 1
    assert wh['max_cluster_count'] == 2
    assert wh['scaling_policy'] == "ECONOMY"
    assert wh['auto_suspend'] == 90
    assert wh['enable_query_acceleration'] == "false"
    assert wh['comment'] == "cde"

    assert wh_params['MAX_CONCURRENCY_LEVEL']['level'] == ""

    assert wh_params['STATEMENT_TIMEOUT_IN_SECONDS']['value'] == "120"
    assert wh_params['STATEMENT_TIMEOUT_IN_SECONDS']['level'] == "WAREHOUSE"


def test_step3(helper):
    wh = helper.show_warehouse("wh001_wh1")

    assert wh is None
