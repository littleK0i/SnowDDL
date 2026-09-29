def test_step1(helper):
    wh = helper.show_warehouse("wh005_wh1")

    assert wh["type"] == "ADAPTIVE"
    assert wh["max_query_performance_level"] == "Small"
    assert wh["query_throughput_multiplier"] == 0


def test_step2(helper):
    wh = helper.show_warehouse("wh005_wh1")

    assert wh["type"] == "ADAPTIVE"
    assert wh["max_query_performance_level"] == "Large"
    assert wh["query_throughput_multiplier"] == 2


def test_step3(helper):
    wh = helper.show_warehouse("wh005_wh1")

    assert wh is None
