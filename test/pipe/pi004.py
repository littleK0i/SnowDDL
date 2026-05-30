def test_step1(helper):
    # Forces automatic creation of pipe via Open Channel call
    open_channel_response = helper.streaming_open_channel("db1", "sc1", "pi004_tb1")
    assert "error_code" not in open_channel_response
    assert "SUCCESS" == open_channel_response["channel_status"]["channel_status_code"]

    table_show = helper.show_table("db1", "sc1", "pi004_tb1")
    pipe_show = helper.show_pipe_streaming("db1", "sc1", "pi004_tb1")

    assert table_show is not None
    assert pipe_show is not None
    assert pipe_show["is_snowflake_managed"] == "true"


def test_step2(helper):
    # Pipe was not dropped
    table_show = helper.show_table("db1", "sc1", "pi004_tb1")
    pipe_show = helper.show_pipe_streaming("db1", "sc1", "pi004_tb1")

    assert table_show is not None
    assert pipe_show is not None


def test_step3(helper):
    # Pipe was automatically dropped with table
    table_show = helper.show_table("db1", "sc1", "pi004_tb1")
    pipe_show = helper.show_pipe_streaming("db1", "sc1", "pi004_tb1")

    assert table_show is None
    assert pipe_show is None
