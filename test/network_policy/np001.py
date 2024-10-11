def test_step1(helper):
    np = helper.show_network_policy("np001_np1")
    np_params = helper.desc_network_policy("np001_np1")
    np_refs = helper.get_network_policy_refs("np001_np1")

    assert np["entries_in_allowed_ip_list"] == 1
    assert np["entries_in_blocked_ip_list"] == 2
    assert np["comment"] == "abc"

    assert np_params["ALLOWED_IP_LIST"]["value"] == "192.168.1.0/24"
    assert np_params["BLOCKED_IP_LIST"]["value"] == "192.168.1.99,192.168.1.100"

    assert len(np_refs) == 1
    assert np_refs[0]["REF_ENTITY_DOMAIN"] == "USER"
    assert str(np_refs[0]["REF_ENTITY_NAME"]).endswith("NP001_US1")


def test_step2(helper):
    np = helper.show_network_policy("np001_np1")
    np_params = helper.desc_network_policy("np001_np1")
    np_refs = helper.get_network_policy_refs("np001_np1")

    assert np["entries_in_allowed_ip_list"] == 1
    assert np["entries_in_blocked_ip_list"] == 1
    assert np["comment"] == "cde"

    assert np_params["ALLOWED_IP_LIST"]["value"] == "192.168.2.0/24"
    assert np_params["BLOCKED_IP_LIST"]["value"] == "192.168.1.99"

    assert len(np_refs) == 0


def test_step3(helper):
    np = helper.show_network_policy("np001_np1")

    assert np is None
