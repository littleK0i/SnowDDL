def test_step1(helper):
    view_01 = helper.desc_view("db1", "sc1", "vw002_vw1")
    view_02 = helper.desc_view("db1", "sc1", "vw002_vw2")

    # Both views exist
    assert view_01
    assert view_02


def test_step2(helper):
    view_01 = helper.desc_view("db1", "sc1", "vw002_vw1")
    view_02 = helper.desc_view("db1", "sc2", "vw002_vw2")

    # Both views exist, second view is now in another schema
    assert view_01
    assert view_02


def test_step3(helper):
    view_01 = helper.desc_view("db1", "sc1", "vw002_vw1")
    view_02 = helper.desc_view("db2", "sc3", "vw002_vw2")

    # Both views exist, second view is now in another database
    assert view_01
    assert view_02
