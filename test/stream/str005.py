def test_step1(helper):
    stream_show = helper.show_stream("db1", "sc1", "str005_str1")

    assert stream_show["source_type"] == "External Table"
    assert stream_show["table_name"].endswith(".STR005_EXT1")
    assert stream_show["mode"] == "INSERT_ONLY"


def test_step2(helper):
    stream_show = helper.show_stream("db1", "sc1", "str005_str1")

    assert stream_show["source_type"] == "Stage"
    assert stream_show["table_name"] == "STR005_ST1"  # Snowflake bug: streams for stages return not fully qualified name
    assert stream_show["mode"] == "DEFAULT"


def test_step3(helper):
    stream_show = helper.show_stream("db1", "sc1", "str005_str1")

    assert stream_show is None
