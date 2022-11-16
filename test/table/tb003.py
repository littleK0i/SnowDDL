def test_step1(helper):
    cols = helper.desc_table("db1", "sc1", "tb003_tb1")

    assert list(cols.keys()) == ["ID", "NAME"]


def test_step2(helper):
    cols = helper.desc_table("db1", "sc1", "tb003_tb1")

    # Some columns were added
    assert list(cols.keys()) == ["ID", "NAME", "STATUS", "REGISTER_TS"]


def test_step3(helper):
    cols = helper.desc_table("db1", "sc1", "tb003_tb1")

    # Some columns were dropped
    assert list(cols.keys()) == ["ID", "STATUS"]
