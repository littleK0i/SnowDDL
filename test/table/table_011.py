def test_011_step1(helper):
    table = helper.show_table("db1", "sc1", "table_011")

    assert table['kind'] == "TRANSIENT"
    assert int(table['retention_time']) == 0

def test_011_step2(helper):
    table = helper.show_table("db1", "sc1", "table_011")

    assert table['kind'] == "TRANSIENT"
    assert int(table['retention_time']) == 1


def test_011_step3(helper):
    table = helper.show_table("db1", "sc1", "table_011")

    assert table['kind'] == "TABLE"
    assert int(table['retention_time']) == 1
