def test_step1(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt004_dt1")
    dynamic_table_desc = helper.desc_table("db1", "sc1", "dt004_dt1")

    assert dynamic_table_show["automatic_clustering"] == "ON"
    assert dynamic_table_show["cluster_by"] == "LINEAR(id)"

    assert dynamic_table_desc["ID"]["comment"] == "aaa"
    assert dynamic_table_desc["NAME"]["comment"] is None


def test_step2(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt004_dt1")
    dynamic_table_desc = helper.desc_table("db1", "sc1", "dt004_dt1")

    assert dynamic_table_show["automatic_clustering"] == "ON"
    assert dynamic_table_show["cluster_by"] == "LINEAR(id, name)"

    assert dynamic_table_desc["ID"]["comment"] is None
    assert dynamic_table_desc["NAME"]["comment"] == "bbb"


def test_step3(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt004_dt1")
    dynamic_table_desc = helper.desc_table("db1", "sc1", "dt004_dt1")

    assert dynamic_table_show["automatic_clustering"] == "OFF"
    assert dynamic_table_show["cluster_by"] == ""

    assert dynamic_table_desc["ID"]["comment"] is None
    assert dynamic_table_desc["NAME"]["comment"] is None
