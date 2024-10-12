def test_step1(helper):
    wh = helper.show_warehouse("wh003_wh1")

    assert wh["size"] == "Medium"
    assert wh["type"] == "SNOWPARK-OPTIMIZED"
    assert wh["min_cluster_count"] == 1
    assert wh["max_cluster_count"] == 1
    assert wh["scaling_policy"] == "STANDARD"
    assert wh["auto_suspend"] == 60
    assert wh["enable_query_acceleration"] == "false"
    assert wh["query_acceleration_max_scale_factor"] == 8
    assert wh["resource_constraint"] == "MEMORY_16X"


def test_step2(helper):
    wh = helper.show_warehouse("wh003_wh1")

    assert wh["size"] == "X-Small"
    assert wh["type"] == "SNOWPARK-OPTIMIZED"
    assert wh["min_cluster_count"] == 1
    assert wh["max_cluster_count"] == 1
    assert wh["scaling_policy"] == "STANDARD"
    assert wh["auto_suspend"] == 60
    assert wh["enable_query_acceleration"] == "false"
    assert wh["query_acceleration_max_scale_factor"] == 8
    assert wh["resource_constraint"] == "MEMORY_1X"


def test_step3(helper):
    wh = helper.show_warehouse("wh003_wh1")

    assert wh["size"] == "Medium"
    assert wh["type"] == "SNOWPARK-OPTIMIZED"
    assert wh["min_cluster_count"] == 1
    assert wh["max_cluster_count"] == 1
    assert wh["scaling_policy"] == "STANDARD"
    assert wh["auto_suspend"] == 60
    assert wh["enable_query_acceleration"] == "false"
    assert wh["query_acceleration_max_scale_factor"] == 8
    assert wh["resource_constraint"] == "MEMORY_16X"
