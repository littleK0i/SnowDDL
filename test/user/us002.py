def test_step1(helper):
    user = helper.show_user("us002_us1")

    assert user["first_name"] == "Jane"
    assert user["last_name"] == "Doe"
    assert user["email"] == "jane@example.com"
    assert user["disabled"] == "true"

    assert user["type"] == "PERSON"
    assert user["has_password"] == "true"
    assert user["has_rsa_public_key"] == "false"


def test_step2(helper):
    user = helper.show_user("us002_us1")

    assert user["first_name"] == ""
    assert user["last_name"] == ""
    assert user["email"] == ""
    assert user["disabled"] == "true"

    assert user["type"] == "LEGACY_SERVICE"
    assert user["has_password"] == "true"
    assert user["has_rsa_public_key"] == "false"


def test_step3(helper):
    user = helper.show_user("us002_us1")

    assert user["first_name"] == ""
    assert user["last_name"] == ""
    assert user["email"] == ""
    assert user["disabled"] == "true"

    assert user["type"] == "SERVICE"
    assert user["has_password"] == "false"
    assert user["has_rsa_public_key"] == "true"
