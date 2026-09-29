def test_step1(helper):
    wh = helper.show_warehouse("wh006_wh1")

    assert wh["type"] == "STANDARD"
    assert wh["size"] == "X-Small"

    assert wh["max_query_performance_level"] is None
    assert wh["query_throughput_multiplier"] is None


def test_step2(helper):
    wh = helper.show_warehouse("wh006_wh1")

    assert wh["type"] == "ADAPTIVE"
    assert wh["size"] is None

    assert wh["max_query_performance_level"] == "Small"
    assert wh["query_throughput_multiplier"] == 2


def test_step3(helper):
    wh = helper.show_warehouse("wh006_wh1")

    assert wh["type"] == "STANDARD"
    assert wh["size"] == "X-Small"

    assert wh["max_query_performance_level"] is None
    assert wh["query_throughput_multiplier"] is None
