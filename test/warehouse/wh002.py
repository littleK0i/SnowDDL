from snowddl import AccountObjectIdent


def test_step1(helper):
    wh = helper.show_warehouse("wh002_wh1")

    assert wh["resource_monitor"] == str(AccountObjectIdent(helper.env_prefix, "wh002_rm1"))


def test_step2(helper):
    wh = helper.show_warehouse("wh002_wh1")

    assert wh["resource_monitor"] == str(AccountObjectIdent(helper.env_prefix, "wh002_rm2"))


def test_step3(helper):
    wh = helper.show_warehouse("wh002_wh1")

    assert wh["resource_monitor"] == "null"
