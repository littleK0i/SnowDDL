def test_step1(helper):
    table1 = helper.show_table("db1", "sc1", f"cu002_tb1")
    table2 = helper.show_table("db1", "sc1", f"cu002_tb2")
    table3 = helper.show_table("db1", "sc1", f"cu002_tb3")

    assert table1 is not None
    assert table2 is not None
    assert table3 is None


def test_step2(helper):
    table1 = helper.show_table("db1", "sc1", f"cu002_tb1")
    table2 = helper.show_table("db1", "sc1", f"cu002_tb2")
    table3 = helper.show_table("db1", "sc1", f"cu002_tb3")

    assert table1 is not None
    assert table2 is None
    assert table3 is not None


def test_step3(helper):
    table1 = helper.show_table("db1", "sc1", f"cu002_tb1")
    table2 = helper.show_table("db1", "sc1", f"cu002_tb2")
    table3 = helper.show_table("db1", "sc1", f"cu002_tb3")

    assert table1 is None
    assert table2 is None
    assert table3 is None
