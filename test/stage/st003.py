def test_step1(helper):
    stage_show = helper.show_stage("db1", "sc1", "st003_st1")

    assert stage_show["type"] == "INTERNAL NO CSE"


def test_step2(helper):
    stage_show = helper.show_stage("db1", "sc1", "st003_st1")

    assert stage_show["type"] == "INTERNAL"


def test_step3(helper):
    stage_show = helper.show_stage("db1", "sc1", "st003_st1")

    assert stage_show["type"] == "INTERNAL"
