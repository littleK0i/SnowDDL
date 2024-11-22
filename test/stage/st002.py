def test_step1(helper):
    stage_show = helper.show_stage("db1", "sc1", "st002_st1")
    stage_desc = helper.desc_stage("db1", "sc1", "st002_st1")

    assert stage_show["type"] == "EXTERNAL"
    assert stage_show["comment"] == "abc"

    assert stage_show["url"] == "gcs://test-bucket1"
    assert stage_show["storage_integration"] == "TEST_STORAGE_INTEGRATION_GCP"

    assert "ST002_FF1" in stage_desc["STAGE_FILE_FORMAT"]["FORMAT_NAME"]["property_value"]

    assert stage_desc["STAGE_COPY_OPTIONS"]["ON_ERROR"]["property_value"] == "SKIP_FILE"
    assert stage_desc["STAGE_COPY_OPTIONS"]["SIZE_LIMIT"]["property_value"] == "25000000"
    assert stage_desc["STAGE_COPY_OPTIONS"]["ENFORCE_LENGTH"]["property_value"] == "false"

    assert stage_desc["DIRECTORY"]["ENABLE"]["property_value"] == "true"
    assert stage_desc["DIRECTORY"]["AUTO_REFRESH"]["property_value"] == "false"


def test_step2(helper):
    stage_show = helper.show_stage("db1", "sc1", "st002_st1")
    stage_desc = helper.desc_stage("db1", "sc1", "st002_st1")

    assert stage_show["type"] == "EXTERNAL"
    assert stage_show["comment"] == "cde"

    assert stage_show["url"] == "gcs://test-bucket2"
    assert stage_show["storage_integration"] == "TEST_STORAGE_INTEGRATION_GCP"

    assert "FORMAT_NAME" not in stage_desc["STAGE_FILE_FORMAT"]

    assert stage_desc["STAGE_COPY_OPTIONS"]["ON_ERROR"]["property_value"] == "ABORT_STATEMENT"
    assert stage_desc["STAGE_COPY_OPTIONS"]["SIZE_LIMIT"]["property_value"] == ""
    assert stage_desc["STAGE_COPY_OPTIONS"]["ENFORCE_LENGTH"]["property_value"] == "true"

    assert stage_desc["DIRECTORY"]["ENABLE"]["property_value"] == "false"


def test_step3(helper):
    stage_show = helper.show_stage("db1", "sc1", "st002_st1")

    assert stage_show is None
