def test_step1(helper):
    sequence = helper.show_sequence("db1", "sc1", "sq001_sq1")

    # Empty comment
    assert not sequence["comment"]

    # Interval and next value are in place
    assert sequence["interval"] == 1
    assert sequence["next_value"] == 10


def test_step2(helper):
    sequence = helper.show_sequence("db1", "sc1", "sq001_sq1")

    # Added comment
    assert sequence["comment"]

    # Interval was changed, but initial value is still the same
    assert sequence["interval"] == 2
    assert sequence["next_value"] == 10


def test_step3(helper):
    sequence = helper.show_sequence("db1", "sc1", "sq001_sq1")

    # Sequence was dropped
    assert sequence is None
