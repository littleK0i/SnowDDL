# ts3 -> ts1,ts4 -> ts2
# ts5 is finalizer
# weird order of tasks is required to test implicit "depends_on"

from json import loads


def test_step1(helper):
    show_1 = helper.show_task("db1", "sc1", "ts002_ts1")
    show_2 = helper.show_task("db1", "sc1", "ts002_ts2")
    show_3 = helper.show_task("db1", "sc1", "ts002_ts3")
    show_4 = helper.show_task("db1", "sc1", "ts002_ts4")
    show_5 = helper.show_task("db1", "sc1", "ts002_ts5")

    assert show_5 is None

    predecessors_1 = loads(show_1["predecessors"])
    predecessors_2 = loads(show_2["predecessors"])
    predecessors_3 = loads(show_3["predecessors"])
    predecessors_4 = loads(show_4["predecessors"])

    assert len(predecessors_1) == 1
    assert str(predecessors_1[0]).endswith(".TS002_TS3")

    assert len(predecessors_2) == 2
    assert str(predecessors_2[0]).endswith(".TS002_TS1")
    assert str(predecessors_2[1]).endswith(".TS002_TS4")

    assert len(predecessors_3) == 0

    assert len(predecessors_4) == 1
    assert str(predecessors_4[0]).endswith(".TS002_TS3")

    assert show_1["condition"] is None
    assert show_2["condition"] == "SYSTEM$GET_PREDECESSOR_RETURN_VALUE('ts002_ts1') >= 1"
    assert show_3["condition"] is None
    assert show_4["condition"] is None


def test_step2(helper):
    show_1 = helper.show_task("db1", "sc1", "ts002_ts1")
    show_2 = helper.show_task("db1", "sc1", "ts002_ts2")
    show_3 = helper.show_task("db1", "sc1", "ts002_ts3")
    show_4 = helper.show_task("db1", "sc1", "ts002_ts4")
    show_5 = helper.show_task("db1", "sc1", "ts002_ts5")

    predecessors_1 = loads(show_1["predecessors"])
    predecessors_2 = loads(show_2["predecessors"])
    predecessors_3 = loads(show_3["predecessors"])
    predecessors_4 = loads(show_4["predecessors"])
    predecessors_5 = loads(show_5["predecessors"])

    assert len(predecessors_1) == 1
    assert str(predecessors_1[0]).endswith(".TS002_TS3")

    assert len(predecessors_2) == 2
    assert str(predecessors_2[0]).endswith(".TS002_TS1")
    assert str(predecessors_2[1]).endswith(".TS002_TS4")

    assert len(predecessors_3) == 0

    assert len(predecessors_4) == 1
    assert str(predecessors_4[0]).endswith(".TS002_TS3")

    assert len(predecessors_5) == 0  # oddly enough, finalizer task does not have predecessors

    assert show_1["condition"] is None
    assert show_2["condition"] == "SYSTEM$GET_PREDECESSOR_RETURN_VALUE('ts002_ts1') >= 0"
    assert show_3["condition"] is None
    assert show_4["condition"] is None
    assert show_5["condition"] is None

    assert show_3["allow_overlapping_execution"] == "true"
    assert show_3["error_integration"] == "TEST_NOTIFICATION_INTEGRATION"


def test_step3(helper):
    show_1 = helper.show_task("db1", "sc1", "ts002_ts1")
    show_2 = helper.show_task("db1", "sc1", "ts002_ts2")
    show_3 = helper.show_task("db1", "sc1", "ts002_ts3")
    show_4 = helper.show_task("db1", "sc1", "ts002_ts4")
    show_5 = helper.show_task("db1", "sc1", "ts002_ts5")

    assert show_1 is None
    assert show_2 is None
    assert show_3 is None
    assert show_4 is None
    assert show_5 is None
