def test_step1(helper):
    cols = helper.desc_table("db1", "sc1", "tb010_tb1")

    assert cols["NAME"]["type"] == "VARCHAR(255)"
    assert cols["NAME"]["expression"] is None

    assert cols["NAME_LENGTH"]["type"] == "NUMBER(38,0)"
    assert cols["NAME_LENGTH"]["expression"] == "LENGTH(NAME)"


def test_step2(helper):
    cols = helper.desc_table("db1", "sc1", "tb010_tb1")

    assert cols["NAME"]["type"] == "VARCHAR(200)"
    assert cols["NAME"]["expression"] is None

    assert cols["NAME_LENGTH"]["type"] == "NUMBER(38,0)"
    assert cols["NAME_LENGTH"]["expression"] == "LENGTH(NAME)"


def test_step3(helper):
    cols = helper.desc_table("db1", "sc1", "tb010_tb1")

    assert cols["NAME"]["type"] == "VARCHAR(200)"
    assert cols["NAME"]["expression"] is None

    assert cols["NAME_LENGTH"]["type"] == "NUMBER(38,0)"
    assert cols["NAME_LENGTH"]["expression"] == "(CAST(LENGTH(NAME) AS NUMBER(18,0))) + 1"
