def test_step1(helper):
    params = helper.desc_authentication_policy("db1", "sc1", "aup002_aup1")

    assert params["MFA_AUTHENTICATION_METHODS"]["value"] == "[PASSWORD, SAML]"
    assert params["MFA_ENROLLMENT"]["value"] == "REQUIRED"


def test_step2(helper):
    params = helper.desc_authentication_policy("db1", "sc1", "aup002_aup1")

    assert params["MFA_ENROLLMENT"]["value"] == "REQUIRED"
    assert params["MFA_AUTHENTICATION_METHODS"]["value"] == "[PASSWORD]"


def test_step3(helper):
    policy_show = helper.show_authentication_policy("db1", "sc1", "aup002_aup1")

    assert policy_show is None
