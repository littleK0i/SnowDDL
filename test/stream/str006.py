def test_step1(helper):
    stream_show = helper.show_stream("db1", "sc1", "str006_str1")

    assert stream_show["source_type"] == "Dynamic Table"
    assert stream_show["table_name"].endswith(".STR006_DT1")
    assert stream_show["comment"] == "abc"


def test_step2(helper):
    stream_show = helper.show_stream("db1", "sc1", "str006_str1")

    assert stream_show["source_type"] == "Dynamic Table"
    assert stream_show["table_name"].endswith(".STR006_DT1")
    assert stream_show["comment"] == "cde"


def test_step3(helper):
    stream_show = helper.show_stream("db1", "sc1", "str006_str1")

    assert stream_show is None
