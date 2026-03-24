def test_step1(helper):
    wh = helper.show_warehouse("wh004_wh1")

    assert wh["size"] == "X-Small"
    assert wh["type"] == "STANDARD"
    assert wh["generation"] == "2"


def test_step2(helper):
    wh = helper.show_warehouse("wh004_wh1")

    assert wh["size"] == "X-Small"
    assert wh["type"] == "STANDARD"
    assert wh["generation"] == "1"


def test_step3(helper):
    wh = helper.show_warehouse("wh004_wh1")

    assert wh["size"] == "X-Small"
    assert wh["type"] == "STANDARD"
    assert wh["generation"] == "1"
