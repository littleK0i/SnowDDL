def test_step1(helper):
    event_table_show = helper.show_event_table("db1", "sc1", "et002_et1")

    assert event_table_show['change_tracking'] == "ON"


def test_step2(helper):
    event_table_show = helper.show_event_table("db1", "sc1", "et002_et1")

    assert event_table_show['change_tracking'] == "OFF"


def test_step3(helper):
    event_table_show = helper.show_event_table("db1", "sc1", "et002_et1")

    assert event_table_show['change_tracking'] == "OFF"
