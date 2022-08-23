def test_004_step1(helper):
    cols = helper.desc_table("db1", "sc1", "table_004")

    assert list(cols.keys()) == ["ID", "NAME"]


def test_004_step2(helper):
    cols = helper.desc_table("db1", "sc1", "table_004")

    # Some columns were added
    assert list(cols.keys()) == ["ID", "STATUS", "NAME", "REGISTER_TS"]


def test_004_step3(helper):
    cols = helper.desc_table("db1", "sc1", "table_004")

    # Some columns were dropped
    assert list(cols.keys()) == ["ID", "STATUS", "DELETE_TS"]
