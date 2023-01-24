def test_step1(helper):
    stage_show = helper.show_stage("db1", "sc1", "st005_st1")

    assert stage_show['type'] == "INTERNAL"


def test_step2(helper):
    stage_show = helper.show_stage("db1", "sc1", "st005_st1")

    assert stage_show['type'] == "EXTERNAL"


def test_step3(helper):
    stage_show = helper.show_stage("db1", "sc1", "st005_st1")

    assert stage_show['type'] == "INTERNAL"
