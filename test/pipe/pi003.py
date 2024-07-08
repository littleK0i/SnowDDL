def test_step1(helper):
    pipe_show = helper.show_pipe("db1", "sc1", "pi003_pi1")

    assert "PI003_TB1" in pipe_show["definition"]
    assert "PI003_ST1" in pipe_show["definition"]
    assert "PI003_FF1" in pipe_show["definition"]

    assert "MATCH_BY_COLUMN_NAME = 'CASE_SENSITIVE'" in pipe_show["definition"]
    assert "INCLUDE_METADATA" in pipe_show["definition"]
    assert "METADATA$FILENAME" in pipe_show["definition"]


def test_step2(helper):
    pipe_show = helper.show_pipe("db1", "sc1", "pi003_pi1")

    assert "PI003_TB1" in pipe_show["definition"]
    assert "PI003_ST1" in pipe_show["definition"]
    assert "PI003_FF1" in pipe_show["definition"]

    assert "MATCH_BY_COLUMN_NAME = 'CASE_INSENSITIVE'" in pipe_show["definition"]
    assert "INCLUDE_METADATA" in pipe_show["definition"]
    assert "METADATA$FILENAME" in pipe_show["definition"]


def test_step3(helper):
    pipe_show = helper.show_pipe("db1", "sc1", "pi003_pi1")

    assert pipe_show is None
