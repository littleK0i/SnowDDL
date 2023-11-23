def test_step1(helper):
    show = helper.show_secret("db1", "sc1", "se004_se1")

    assert show["secret_type"] == "OAUTH2"


def test_step2(helper):
    show = helper.show_secret("db1", "sc1", "se004_se1")

    assert show["secret_type"] == "OAUTH2"


def test_step3(helper):
    show = helper.show_secret("db1", "sc1", "se004_se1")

    assert show is None
