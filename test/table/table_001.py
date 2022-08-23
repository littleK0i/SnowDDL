def test_001_step1(helper):
    cols = helper.desc_table("db1", "sc1", "table_001")

    # Created table with specific number of columns
    assert len(cols) == 23

    # Data types and sizes
    assert cols['NUM1']['type'] == "NUMBER(10,0)"
    assert cols['NUM2']['type'] == "NUMBER(38,0)"
    assert cols['VAR1']['type'] == "VARCHAR(10)"


def test_001_step2(helper):
    cols = helper.desc_table("db1", "sc1", "table_001")

    # Still the same number of columns
    assert len(cols) == 23

    # Data types and sizes
    assert cols['NUM1']['type'] == "NUMBER(12,0)"
    assert cols['NUM2']['type'] == "NUMBER(36,0)"
    assert cols['VAR1']['type'] == "VARCHAR(100)"


def test_001_step3(helper):
    table = helper.show_table("db1", "sc1", "table_001")

    # Table was dropped
    assert table is None
