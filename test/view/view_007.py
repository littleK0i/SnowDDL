def test_007_step1(helper):
    view_01 = helper.desc_view("db1", "sc1", "view_007_01")
    view_02 = helper.desc_view("db1", "sc1", "view_007_02")

    # Both views exist
    assert view_01
    assert view_02


def test_007_step2(helper):
    view_01 = helper.desc_view("db1", "sc1", "view_007_01")
    view_02 = helper.desc_view("db1", "sc2", "view_007_02")

    # Both views exist, second view is now in another schema
    assert view_01
    assert view_02


def test_007_step3(helper):
    view_01 = helper.desc_view("db1", "sc1", "view_007_01")
    view_02 = helper.desc_view("db2", "sc3", "view_007_02")

    # Both views exist, second view is now in another database
    assert view_01
    assert view_02
