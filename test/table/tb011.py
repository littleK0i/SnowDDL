def test_step1(helper):
    cols = helper.desc_table("db1", "sc1", "tb011_tb1")

    assert cols["NUM1"]["type"] == "NUMBER(10,0)"
    assert cols["NUM2"]["type"] == "NUMBER(38,0)"
    assert cols["NUM3"]["type"] == "NUMBER(10,5)"
    assert cols["NUM4"]["type"] == "NUMBER(38,5)"


def test_step2(helper):
    cols = helper.desc_table("db1", "sc1", "tb011_tb1")

    # Expect ALTER, change only precision, scale remains the same
    assert cols["NUM1"]["type"] == "NUMBER(12,0)"
    assert cols["NUM2"]["type"] == "NUMBER(36,0)"
    assert cols["NUM3"]["type"] == "NUMBER(12,5)"
    assert cols["NUM4"]["type"] == "NUMBER(36,5)"


def test_step3(helper):
    cols = helper.desc_table("db1", "sc1", "tb011_tb1")

    # Expect REPLACE, change scale
    assert cols["NUM1"]["type"] == "NUMBER(12,2)"
    assert cols["NUM2"]["type"] == "NUMBER(36,2)"
    assert cols["NUM3"]["type"] == "NUMBER(12,0)"
    assert cols["NUM4"]["type"] == "NUMBER(36,0)"
