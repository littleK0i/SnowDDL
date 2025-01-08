def test_step1(helper):
    stream_show = helper.show_stream("db1", "sc1", "str002_str1")

    assert stream_show["source_type"] == "Table"
    assert stream_show["table_name"].endswith(".STR002_TB1")
    assert stream_show["mode"] == "DEFAULT"
    assert stream_show["comment"] == ""


def test_step2(helper):
    stream_show = helper.show_stream("db1", "sc1", "str002_str1")

    assert stream_show["source_type"] == "Table"
    assert stream_show["table_name"].endswith(".STR002_TB1")
    assert stream_show["mode"] == "DEFAULT"
    assert stream_show["comment"] == ""


def test_step3(helper):
    stream_show = helper.show_stream("db1", "sc1", "str002_str1")

    assert stream_show["source_type"] == "Table"
    assert stream_show["table_name"].endswith(".STR002_TB2")
    assert stream_show["mode"] == "DEFAULT"
    assert stream_show["comment"] == ""
