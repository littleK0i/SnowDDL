def test_step1(helper):
    params = helper.desc_authentication_policy("db1", "sc1", "aup003_aup1")

    assert params["AUTHENTICATION_METHODS"]["value"] == "[SAML, KEYPAIR]"
    assert params["MFA_ENROLLMENT"]["value"] == "REQUIRED_PASSWORD_ONLY"

    assert "ALLOWED_METHODS=[PASSKEY, DUO]" in params["MFA_POLICY"]["value"]

    assert "DEFAULT_EXPIRY_IN_DAYS=30" in params["PAT_POLICY"]["value"]
    assert "MAX_EXPIRY_IN_DAYS=365" in params["PAT_POLICY"]["value"]
    assert "NETWORK_POLICY_EVALUATION=ENFORCED_NOT_REQUIRED" in params["PAT_POLICY"]["value"]

    assert "ALLOWED_PROVIDERS=[AWS, AZURE, GCP, OIDC]" in params["WORKLOAD_IDENTITY_POLICY"]["value"]
    assert "ALLOWED_AWS_ACCOUNTS=[123456789012, 210987654321]" in params["WORKLOAD_IDENTITY_POLICY"]["value"]
    assert "ALLOWED_AZURE_ISSUERS=[https://login.microsoftonline.com/8c7832f5-de56-4d9f-ba94-3b2c361abe6b/v2.0, https://login.microsoftonline.com/9ebd1ec9-9a78-4429-8f53-5cf870a812d1/v2.0]" in params["WORKLOAD_IDENTITY_POLICY"]["value"]
    assert "ALLOWED_OIDC_ISSUERS=[https://my.custom.oidc.issuer/, https://another.custom/oidc/issuer]" in params["WORKLOAD_IDENTITY_POLICY"]["value"]


def test_step2(helper):
    params = helper.desc_authentication_policy("db1", "sc1", "aup003_aup1")

    assert params["AUTHENTICATION_METHODS"]["value"] == "[SAML, KEYPAIR]"
    assert params["MFA_ENROLLMENT"]["value"] == "REQUIRED_PASSWORD_ONLY"

    assert "ALLOWED_METHODS=[ALL]" in params["MFA_POLICY"]["value"]

    assert "DEFAULT_EXPIRY_IN_DAYS=15" in params["PAT_POLICY"]["value"]
    assert "MAX_EXPIRY_IN_DAYS=365" in params["PAT_POLICY"]["value"]
    assert "NETWORK_POLICY_EVALUATION=ENFORCED_REQUIRED" in params["PAT_POLICY"]["value"]

    assert "ALLOWED_PROVIDERS=[ALL]" in params["WORKLOAD_IDENTITY_POLICY"]["value"]
    assert "ALLOWED_AWS_ACCOUNTS=[ALL]" in params["WORKLOAD_IDENTITY_POLICY"]["value"]
    assert "ALLOWED_AZURE_ISSUERS=[ALL]" in params["WORKLOAD_IDENTITY_POLICY"]["value"]
    assert "ALLOWED_OIDC_ISSUERS=[ALL]" in params["WORKLOAD_IDENTITY_POLICY"]["value"]


def test_step3(helper):
    params = helper.desc_authentication_policy("db1", "sc1", "aup003_aup1")

    assert params["AUTHENTICATION_METHODS"]["value"] == "[SAML, KEYPAIR]"
    assert params["MFA_ENROLLMENT"]["value"] == "REQUIRED_PASSWORD_ONLY"

    assert "ALLOWED_METHODS=[PASSKEY, DUO]" in params["MFA_POLICY"]["value"]

    assert "DEFAULT_EXPIRY_IN_DAYS=10" in params["PAT_POLICY"]["value"]
    assert "MAX_EXPIRY_IN_DAYS=180" in params["PAT_POLICY"]["value"]
    assert "NETWORK_POLICY_EVALUATION=ENFORCED_REQUIRED" in params["PAT_POLICY"]["value"]

    assert "ALLOWED_PROVIDERS=[AWS]" in params["WORKLOAD_IDENTITY_POLICY"]["value"]
    assert "ALLOWED_AWS_ACCOUNTS=[123456789012]" in params["WORKLOAD_IDENTITY_POLICY"]["value"]
    assert "ALLOWED_AZURE_ISSUERS=[ALL]" in params["WORKLOAD_IDENTITY_POLICY"]["value"]
    assert "ALLOWED_OIDC_ISSUERS=[https://my.custom.oidc.issuer/, https://another.custom/oidc/issuer]" in params["WORKLOAD_IDENTITY_POLICY"]["value"]
