def test_003_step1(helper):
    cols = helper.desc_table("db1", "sc1", "table_003")

    assert list(cols.keys()) == ["ID", "NAME"]


def test_003_step2(helper):
    cols = helper.desc_table("db1", "sc1", "table_003")

    # Some columns were added
    assert list(cols.keys()) == ["ID", "NAME", "STATUS", "REGISTER_TS"]


def test_003_step3(helper):
    cols = helper.desc_table("db1", "sc1", "table_003")

    # Some columns were dropped
    assert list(cols.keys()) == ["ID", "STATUS"]
