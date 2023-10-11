def test_step1(helper):
    file_format_show = helper.show_file_format("db1", "sc1", "ff002_ff1")
    file_format_desc = helper.desc_file_format("db1", "sc1", "ff002_ff1")

    assert file_format_show["type"] == "AVRO"

    assert file_format_desc["COMPRESSION"]["property_value"] == "ZSTD"


def test_step2(helper):
    file_format_show = helper.show_file_format("db1", "sc1", "ff002_ff1")
    file_format_desc = helper.desc_file_format("db1", "sc1", "ff002_ff1")

    assert file_format_show["type"] == "PARQUET"

    assert file_format_desc["COMPRESSION"]["property_value"] == "SNAPPY"


def test_step3(helper):
    file_format_show = helper.show_file_format("db1", "sc1", "ff002_ff1")

    assert file_format_show["type"] == "ORC"
