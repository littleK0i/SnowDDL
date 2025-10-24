def test_step1(helper):
    params = helper.desc_authentication_policy("db1", "sc1", "aup001_aup1")
    refs = helper.get_policy_refs("db1", "sc1", "aup001_aup1")

    assert params["AUTHENTICATION_METHODS"]["value"] == "[SAML, KEYPAIR]"
    assert params["MFA_ENROLLMENT"]["value"] == "REQUIRED"
    assert params["CLIENT_TYPES"]["value"] == "[SNOWFLAKE_UI, DRIVERS]"
    assert params["SECURITY_INTEGRATIONS"]["value"] == "[ALL]"
    assert str(params["COMMENT"]["value"]).startswith("abc #")

    assert len(refs) == 1
    assert refs[0]["REF_ENTITY_DOMAIN"] == "USER"
    assert str(refs[0]["REF_ENTITY_NAME"]).endswith("AUP001_US1")


def test_step2(helper):
    params = helper.desc_authentication_policy("db1", "sc1", "aup001_aup1")
    refs_1 = helper.get_policy_refs("db1", "sc1", "aup001_aup1")
    refs_2 = helper.get_policy_refs("db1", "sc1", "aup001_aup2")

    assert params["AUTHENTICATION_METHODS"]["value"] == "[SAML, PASSWORD]"
    assert params["MFA_ENROLLMENT"]["value"] == "REQUIRED_SNOWFLAKE_UI_PASSWORD_ONLY"  # orig: OPTIONAL
    assert params["CLIENT_TYPES"]["value"] == "[SNOWFLAKE_UI, SNOWSQL]"
    assert params["SECURITY_INTEGRATIONS"]["value"] == "[ALL]"
    assert str(params["COMMENT"]["value"]).startswith("cde #")

    assert len(refs_1) == 0
    assert len(refs_2) == 1

    assert refs_2[0]["REF_ENTITY_DOMAIN"] == "USER"
    assert str(refs_2[0]["REF_ENTITY_NAME"]).endswith("AUP001_US1")


def test_step3(helper):
    params = helper.desc_authentication_policy("db1", "sc1", "aup001_aup1")
    refs = helper.get_policy_refs("db1", "sc1", "aup001_aup1")

    assert params["AUTHENTICATION_METHODS"]["value"] == "[ALL]"
    assert params["MFA_ENROLLMENT"]["value"] == "REQUIRED_SNOWFLAKE_UI_PASSWORD_ONLY"  # orig: OPTIONAL
    assert params["CLIENT_TYPES"]["value"] == "[ALL]"
    assert params["SECURITY_INTEGRATIONS"]["value"] == "[ALL]"
    assert str(params["COMMENT"]["value"]).startswith("#")

    assert len(refs) == 0
