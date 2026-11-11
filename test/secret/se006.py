def test_step1(helper):
    show = helper.show_secret("db1", "sc1", "se006_se1")

    assert show["secret_type"] == "WORKLOAD_IDENTITY_FEDERATION"
    assert show["comment"] == "abc"


def test_step2(helper):
    show = helper.show_secret("db1", "sc1", "se006_se1")

    assert show["secret_type"] == "WORKLOAD_IDENTITY_FEDERATION"
    assert show["comment"] == "cde"


def test_step3(helper):
    show = helper.show_secret("db1", "sc1", "se006_se1")

    assert show is None
