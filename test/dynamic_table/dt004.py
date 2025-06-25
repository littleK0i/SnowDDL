def test_step1(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt004_dt1")

    assert dynamic_table_show["automatic_clustering"] == "ON"
    assert dynamic_table_show["cluster_by"] == "LINEAR(id)"


def test_step2(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt004_dt1")

    assert dynamic_table_show["automatic_clustering"] == "ON"
    assert dynamic_table_show["cluster_by"] == "LINEAR(id, name)"


def test_step3(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt004_dt1")

    assert dynamic_table_show["automatic_clustering"] == "OFF"
    assert dynamic_table_show["cluster_by"] == ""
