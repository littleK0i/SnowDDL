def test_step1(helper):
    params = helper.desc_authentication_policy("db1", "sc1", "aup002_aup1")

    assert params["AUTHENTICATION_METHODS"]["value"] == "[PASSWORD, SAML]"
    assert params["MFA_ENROLLMENT"]["value"] == "REQUIRED"
    assert params["CLIENT_TYPES"]["value"] == "[ALL]"
    assert params["CLIENT_POLICY"]["value"] == "{JDBC_DRIVER={MINIMUM_VERSION=3.20.0}, PYTHON_DRIVER={MINIMUM_VERSION=4.0.0}}"
    assert params["SECURITY_INTEGRATIONS"]["value"] == "[ALL]"


def test_step2(helper):
    params = helper.desc_authentication_policy("db1", "sc1", "aup002_aup1")

    assert params["AUTHENTICATION_METHODS"]["value"] == "[ALL]"
    assert params["MFA_ENROLLMENT"]["value"] == "REQUIRED"
    assert params["CLIENT_TYPES"]["value"] == "[ALL]"
    assert params["CLIENT_POLICY"]["value"] == "{PYTHON_DRIVER={MINIMUM_VERSION=4.1.0}}"
    assert params["SECURITY_INTEGRATIONS"]["value"] == "[ALL]"


def test_step3(helper):
    policy_show = helper.show_authentication_policy("db1", "sc1", "aup002_aup1")

    assert policy_show is None
