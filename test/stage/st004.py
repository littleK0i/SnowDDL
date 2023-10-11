def test_step1(helper):
    stage_show = helper.show_stage("db1", "sc1", "st004_st1")

    assert stage_show["has_encryption_key"] == "Y"


def test_step2(helper):
    stage_show = helper.show_stage("db1", "sc1", "st004_st1")

    assert stage_show["has_encryption_key"] == "N"


def test_step3(helper):
    stage_show = helper.show_stage("db1", "sc1", "st004_st1")

    assert stage_show["has_encryption_key"] == "Y"
