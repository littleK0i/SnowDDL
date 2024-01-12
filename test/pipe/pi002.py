def test_step1(helper):
    pipe_show = helper.show_pipe("db1", "sc1", "pi002_pi1")

    assert "PI002_TB1" in pipe_show["definition"]
    assert "PI002_ST1" in pipe_show["definition"]
    assert "PI002_FF1" in pipe_show["definition"]

    assert '"/abc/cde' in pipe_show["definition"]
    assert "ENFORCE_LENGTH = TRUE" in pipe_show["definition"]


def test_step2(helper):
    pipe_show = helper.show_pipe("db1", "sc1", "pi002_pi1")

    assert "PI002_TB1" in pipe_show["definition"]
    assert "PI002_ST1" in pipe_show["definition"]
    assert "PI002_FF1" in pipe_show["definition"]

    assert '"/abc/cde/fgh' in pipe_show["definition"]
    assert "ENFORCE_LENGTH = FALSE" in pipe_show["definition"]


def test_step3(helper):
    pipe_show = helper.show_pipe("db1", "sc1", "pi002_pi1")

    assert pipe_show is None
