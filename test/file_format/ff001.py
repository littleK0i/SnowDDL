def test_step1(helper):
    file_format_show = helper.show_file_format("db1", "sc1", "ff001_ff1")
    file_format_desc = helper.desc_file_format("db1", "sc1", "ff001_ff1")

    assert file_format_show["type"] == "CSV"

    assert file_format_desc["COMPRESSION"]["property_value"] == "GZIP"
    assert file_format_desc["RECORD_DELIMITER"]["property_value"] == "\\n"
    assert file_format_desc["FIELD_DELIMITER"]["property_value"] == ","
    assert file_format_desc["SKIP_HEADER"]["property_value"] == "1"
    assert file_format_desc["TRIM_SPACE"]["property_value"] == "true"

    # Validate fact that short hash is present
    assert file_format_show["comment"].startswith("abc #")


def test_step2(helper):
    file_format_show = helper.show_file_format("db1", "sc1", "ff001_ff1")
    file_format_desc = helper.desc_file_format("db1", "sc1", "ff001_ff1")

    assert file_format_show["type"] == "CSV"

    assert file_format_desc["COMPRESSION"]["property_value"] == "DEFLATE"
    assert file_format_desc["RECORD_DELIMITER"]["property_value"] == "\\t"
    assert file_format_desc["FIELD_DELIMITER"]["property_value"] == ";"
    assert file_format_desc["SKIP_HEADER"]["property_value"] == "2"
    assert file_format_desc["TRIM_SPACE"]["property_value"] == "false"

    # Validate fact that short hash is present
    assert file_format_show["comment"].startswith("cde #")


def test_step3(helper):
    file_format_show = helper.show_file_format("db1", "sc1", "ff001_ff1")

    assert file_format_show is None
