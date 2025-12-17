def test_step1(helper):
    cols = helper.desc_table("db1", "sc1", "tb001_tb1")

    # Created table with specific number of columns
    assert len(cols) == 25

    # Data types and sizes
    assert cols["NUM1"]["type"] == "NUMBER(10,0)"
    assert cols["NUM2"]["type"] == "NUMBER(38,0)"
    assert cols["VAR1"]["type"] == "VARCHAR(10)"


def test_step2(helper):
    cols = helper.desc_table("db1", "sc1", "tb001_tb1")

    # Still the same number of columns
    assert len(cols) == 25

    # Data types and sizes
    assert cols["NUM1"]["type"] == "NUMBER(12,0)"
    assert cols["NUM2"]["type"] == "NUMBER(36,0)"
    assert cols["VAR1"]["type"] == "VARCHAR(100)"


def test_step3(helper):
    table = helper.show_table("db1", "sc1", "tb001_tb1")

    # Table was dropped
    assert table is None
