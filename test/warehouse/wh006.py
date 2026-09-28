def test_step1(helper):
    wh = helper.show_warehouse("wh006_wh1")

    assert wh["type"] == "STANDARD"
    assert wh["size"] == "X-Small"


def test_step2(helper):
    wh = helper.show_warehouse("wh006_wh1")

    assert wh["type"] == "ADAPTIVE"
    assert wh["max_query_performance_level"] == "Small"


def test_step3(helper):
    wh = helper.show_warehouse("wh006_wh1")

    assert wh["type"] == "STANDARD"
    assert wh["size"] == "X-Small"
