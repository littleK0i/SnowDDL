def test_step1(helper):
    table_show = helper.show_table("db1", "sc1", "dt003_dt1")
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt003_dt1")

    assert table_show["kind"] == "TRANSIENT"
    assert table_show["retention_time"] == "0"

    assert dynamic_table_show["automatic_clustering"] == "ON"
    assert dynamic_table_show["cluster_by"] == "LINEAR(type, sub_type)"

    assert "refresh_mode = 'INCREMENTAL'" in dynamic_table_show["text"]
    assert "initialize = 'ON_SCHEDULE'" in dynamic_table_show["text"]


def test_step2(helper):
    table_show = helper.show_table("db1", "sc1", "dt003_dt1")
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt003_dt1")

    assert table_show["kind"] == "TRANSIENT"
    assert table_show["retention_time"] == "1"

    assert dynamic_table_show["automatic_clustering"] == "OFF"
    assert dynamic_table_show["cluster_by"] == ""

    assert "refresh_mode = 'FULL'" in dynamic_table_show["text"]
    assert "initialize = 'ON_CREATE'" in dynamic_table_show["text"]

    table_desc = helper.desc_table("db1", "sc1", "dt003_dt1")

    assert table_desc["TYPE"]["comment"] == "Type"
    assert table_desc["SUB_TYPE"]["comment"] == "Sub-Type"
    assert table_desc["CNT"]["comment"] is None


def test_step3(helper):
    dynamic_table_show = helper.show_dynamic_table("db1", "sc1", "dt003_dt1")

    assert dynamic_table_show is None
