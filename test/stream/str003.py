def test_step1(helper):
    stream_show = helper.show_stream("db1", "sc1", "str003_str1")

    assert stream_show["source_type"] == "View"
    assert stream_show["table_name"].endswith(".STR003_VW1")
    assert stream_show["mode"] == "DEFAULT"
    assert stream_show["comment"] == ""


def test_step2(helper):
    stream_show = helper.show_stream("db1", "sc1", "str003_str1")

    assert stream_show["source_type"] == "View"
    assert stream_show["table_name"].endswith(".STR003_VW1")
    assert stream_show["mode"] == "DEFAULT"
    assert stream_show["comment"] == ""


def test_step3(helper):
    stream_show = helper.show_stream("db1", "sc1", "str003_str1")

    assert stream_show is None
