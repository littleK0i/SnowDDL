def test_step1(helper):
    user = helper.show_user("us003_us1")

    assert user["disabled"] == "true"
    assert user["type"] == "SERVICE"
    assert user["has_password"] == "false"
    assert user["has_rsa_public_key"] == "false"
    assert user["has_workload_identity"] == "true"


def test_step2(helper):
    user = helper.show_user("us003_us1")

    assert user["disabled"] == "true"
    assert user["type"] == "PERSON"
    assert user["has_password"] == "false"
    assert user["has_rsa_public_key"] == "false"
    assert user["has_workload_identity"] == "false"


def test_step3(helper):
    user = helper.show_user("us003_us1")

    assert user["disabled"] == "true"
    assert user["type"] == "SERVICE"
    assert user["has_password"] == "false"
    assert user["has_rsa_public_key"] == "false"
    assert user["has_workload_identity"] == "true"
