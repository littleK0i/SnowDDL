def test_step1(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt005_dt1")

    assert dynamic_table_show["scheduler"] == "DISABLE"
    assert dynamic_table_show["target_lag"] == ""


def test_step2(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt005_dt1")

    assert dynamic_table_show["scheduler"] == "ENABLE"
    assert dynamic_table_show["target_lag"] == "1 day"


def test_step3(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt005_dt1")

    assert dynamic_table_show["scheduler"] == "DISABLE"
    assert dynamic_table_show["target_lag"] == ""
