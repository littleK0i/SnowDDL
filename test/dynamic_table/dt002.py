def test_step1(helper):
    dynamic_table_show_1 = helper.show_dynamic_table("db1", "sc1", "dt002_dt1")
    dynamic_table_show_2 = helper.show_dynamic_table("db1", "sc1", "dt002_dt2")

    assert dynamic_table_show_1['target_lag'] == "DOWNSTREAM"
    assert "count(*) AS cnt" in dynamic_table_show_1['text']
    assert "dt002_tb1" in dynamic_table_show_1['text']

    assert dynamic_table_show_2['target_lag'] == "5 minutes"
    assert "count(*) AS cnt" in dynamic_table_show_2['text']
    assert "dt002_dt1" in dynamic_table_show_2['text']


def test_step2(helper):
    dynamic_table_show_1 = helper.show_dynamic_table("db1", "sc1", "dt002_dt1")
    dynamic_table_show_2 = helper.show_dynamic_table("db1", "sc1", "dt002_dt2")

    assert dynamic_table_show_1['target_lag'] == "DOWNSTREAM"
    assert "count(*) AS name_cnt" in dynamic_table_show_1['text']
    assert "dt002_tb2" in dynamic_table_show_1['text']

    assert dynamic_table_show_2['target_lag'] == "5 minutes"
    assert "count(*) AS item_cnt" in dynamic_table_show_2['text']
    assert "dt002_dt1" in dynamic_table_show_2['text']


def test_step3(helper):
    dynamic_table_show_1 = helper.show_dynamic_table("db1", "sc1", "dt002_dt1")
    dynamic_table_show_2 = helper.show_dynamic_table("db1", "sc1", "dt002_dt2")

    assert dynamic_table_show_1['target_lag'] == "DOWNSTREAM"
    assert "count(*) AS name_cnt" in dynamic_table_show_1['text']
    assert "dt002_tb2" in dynamic_table_show_1['text']

    assert dynamic_table_show_2['target_lag'] == "5 minutes"
    assert "count(*) AS item_cnt" in dynamic_table_show_2['text']
    assert "dt002_dt1" in dynamic_table_show_2['text']
