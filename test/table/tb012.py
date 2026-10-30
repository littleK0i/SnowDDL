def test_step1(helper):
    # Enabled on create
    table = helper.show_table("db1", "sc1", "tb012_tb1")
    assert table["error_logging"] == "ON"

    table = helper.show_table("db1", "sc1", "tb012_tb2")
    assert table["error_logging"] == "ON"

    # Disabled on create
    table = helper.show_table("db1", "sc1", "tb012_tb3")
    assert table["error_logging"] == "OFF"


def test_step2(helper):
    # Param removed from config, value is preserved
    table = helper.show_table("db1", "sc1", "tb012_tb1")
    assert table["error_logging"] == "ON"

    # Expect REPLACE, error logging is preserved
    table = helper.show_table("db1", "sc1", "tb012_tb2")
    cols = helper.desc_table("db1", "sc1", "tb012_tb2")

    assert cols["ID"]["type"] == "NUMBER(10,2)"
    assert table["error_logging"] == "ON"

    table = helper.show_table("db1", "sc1", "tb012_tb3")
    assert table["error_logging"] == "OFF"


def test_step3(helper):
    # Disabled
    table = helper.show_table("db1", "sc1", "tb012_tb1")
    assert table["error_logging"] == "OFF"

    # No changes
    table = helper.show_table("db1", "sc1", "tb012_tb2")
    assert table["error_logging"] == "ON"

    table = helper.show_table("db1", "sc1", "tb012_tb3")
    assert table["error_logging"] == "OFF"
