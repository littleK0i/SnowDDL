def test_step1(helper):
    show = helper.show_external_access_integration("eai001_eai1")
    desc = helper.desc_external_access_integration("eai001_eai1")

    assert show["type"] == "EXTERNAL_ACCESS"
    assert show["enabled"] == "true"
    assert str(show["comment"]).startswith("abc #")

    assert "EAI001_SE1" in desc["ALLOWED_AUTHENTICATION_SECRETS"]
    assert "EAI001_SE2" in desc["ALLOWED_AUTHENTICATION_SECRETS"]

    assert "EAI001_NR1" in desc["ALLOWED_NETWORK_RULES"]
    assert "EAI001_NR2" in desc["ALLOWED_NETWORK_RULES"]

    assert "[TEST_API_SECURITY_INTEGRATION]" == desc["ALLOWED_API_AUTHENTICATION_INTEGRATIONS"]


def test_step2(helper):
    show = helper.show_external_access_integration("eai001_eai1")
    desc = helper.desc_external_access_integration("eai001_eai1")

    assert show["type"] == "EXTERNAL_ACCESS"
    assert show["enabled"] == "true"
    assert str(show["comment"]).startswith("cde #")

    assert "EAI001_SE1" in desc["ALLOWED_AUTHENTICATION_SECRETS"]
    assert "EAI001_SE2" in desc["ALLOWED_AUTHENTICATION_SECRETS"]

    assert "EAI001_NR1" in desc["ALLOWED_NETWORK_RULES"]
    assert "EAI001_NR2" in desc["ALLOWED_NETWORK_RULES"]

    assert "[TEST_API_SECURITY_INTEGRATION]" == desc["ALLOWED_API_AUTHENTICATION_INTEGRATIONS"]


def test_step3(helper):
    show = helper.show_external_access_integration("eai001_eai1")

    assert show is None
