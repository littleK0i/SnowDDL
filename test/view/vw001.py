def test_step1(helper):
    cols = helper.desc_view("db1", "sc1", "vw001_vw1")
    view = helper.show_view("db1", "sc1", "vw001_vw1")

    # Created view with specific number of columns
    assert len(cols) == 2

    # Empty view comment
    assert not view["comment"]

    # Empty column comments
    assert not cols["ID"]["comment"]
    assert not cols["NAME"]["comment"]

    # Not secure
    assert view["is_secure"] == "false"


def test_step2(helper):
    cols = helper.desc_view("db1", "sc1", "vw001_vw1")
    view = helper.show_view("db1", "sc1", "vw001_vw1")

    # Added transformation column
    assert len(cols) == 3

    # Added view comment
    assert view["comment"]

    # Added column comments
    assert cols["ID"]["comment"]
    assert cols["NAME"]["comment"]

    # Secure view
    assert view["is_secure"] == "true"


def test_step3(helper):
    view = helper.show_view("db1", "sc1", "vw001_vw1")

    # Table was dropped
    assert view is None
