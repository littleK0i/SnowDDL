def test_step1(helper):
    show = helper.show_secret("db1", "sc1", "se005_se1")

    assert show["secret_type"] == "SYMMETRIC_KEY"
    assert show["comment"] == "abc"


def test_step2(helper):
    show = helper.show_secret("db1", "sc1", "se005_se1")

    assert show["secret_type"] == "SYMMETRIC_KEY"
    assert show["comment"] == "cde"


def test_step3(helper):
    show = helper.show_secret("db1", "sc1", "se005_se1")

    assert show is None
