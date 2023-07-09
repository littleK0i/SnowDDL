def test_step1(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt001_dt1")

    assert str(dynamic_table_show['warehouse']).endswith("__DT001_WH1")
    assert dynamic_table_show['target_lag'] == "1 minute"
    assert dynamic_table_show['comment'] == "abc"


def test_step2(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt001_dt1")

    assert str(dynamic_table_show['warehouse']).endswith("__DT001_WH2")
    assert dynamic_table_show['target_lag'] == "2 days"
    assert dynamic_table_show['comment'] == "cde"


def test_step3(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt001_dt1")

    assert dynamic_table_show is None
