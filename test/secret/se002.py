def test_step1(helper):
    show = helper.show_secret("db1", "sc1", "se002_se1")

    assert show["secret_type"] == "PASSWORD"


def test_step2(helper):
    show = helper.show_secret("db1", "sc1", "se002_se1")

    assert show["secret_type"] == "PASSWORD"


def test_step3(helper):
    show = helper.show_secret("db1", "sc1", "se002_se1")

    assert show is None
