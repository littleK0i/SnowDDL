def test_step1(helper):
    show = helper.show_secret("db1", "sc1", "se003_se1")

    assert show["secret_type"] == "OAUTH2"
    assert show["oauth_scopes"] == "[photo, offline_access]"


def test_step2(helper):
    show = helper.show_secret("db1", "sc1", "se003_se1")

    assert show["secret_type"] == "OAUTH2"
    assert show["oauth_scopes"] == "[photo]"


def test_step3(helper):
    show = helper.show_secret("db1", "sc1", "se003_se1")

    assert show is None
