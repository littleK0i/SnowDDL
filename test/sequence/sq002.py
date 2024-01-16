def test_step1(helper):
    sequence = helper.show_sequence("db1", "sc1", "sq002_sq1")

    assert sequence["ordered"] == "Y"


def test_step2(helper):
    sequence = helper.show_sequence("db1", "sc1", "sq002_sq1")

    assert sequence["ordered"] == "N"


def test_step3(helper):
    sequence = helper.show_sequence("db1", "sc1", "sq002_sq1")

    assert sequence is None
