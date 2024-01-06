def test_step1(helper):
    pipe_show = helper.show_pipe("db1", "sc1", "pi001_pi1")

    assert "PI001_TB1" in pipe_show["definition"]
    assert "PI001_ST1" in pipe_show["definition"]

    assert pipe_show["error_integration"] is None
    assert pipe_show["pattern"] == ".*[.]csv"

    assert pipe_show["comment"].startswith("abc #")


def test_step2(helper):
    pipe_show = helper.show_pipe("db1", "sc1", "pi001_pi1")

    assert "PI001_TB1" in pipe_show["definition"]
    assert "PI001_ST1" in pipe_show["definition"]

    assert pipe_show["error_integration"] == "TEST_NOTIFICATION_INTEGRATION"
    assert pipe_show["pattern"] == ".*[.]csv[.]gz"

    assert pipe_show["comment"].startswith("cde #")


def test_step3(helper):
    pipe_show = helper.show_pipe("db1", "sc1", "pi001_pi1")

    assert pipe_show is None
