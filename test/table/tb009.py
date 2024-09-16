def test_step1(helper):
    cols = helper.desc_table("db1", "sc1", "tb009_tb1")

    assert cols["VEC1"]["type"] == "VECTOR(INT, 16)"
    assert cols["VEC2"]["type"] == "VECTOR(INT, 4096)"
    assert cols["VEC3"]["type"] == "VECTOR(FLOAT, 32)"
    assert cols["VEC4"]["type"] == "VECTOR(FLOAT, 4096)"


def test_step2(helper):
    cols = helper.desc_table("db1", "sc1", "tb009_tb1")

    assert cols["VEC1"]["type"] == "VECTOR(INT, 32)"
    assert cols["VEC2"]["type"] == "VECTOR(FLOAT, 4096)"
    assert cols["VEC3"]["type"] == "VECTOR(INT, 64)"
    assert cols["VEC4"]["type"] == "VECTOR(FLOAT, 128)"


def test_step3(helper):
    table = helper.show_table("db1", "sc1", "tb009_tb1")

    # Table was dropped
    assert table is None
