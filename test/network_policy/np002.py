from json import loads


def test_step1(helper):
    np = helper.show_network_policy("np002_np1")
    np_params = helper.desc_network_policy("np002_np1")

    assert np["entries_in_allowed_network_rules"] == 2
    assert np["entries_in_allowed_network_rules"] == 2

    allowed_network_rule_list = sorted(v["fullyQualifiedRuleName"] for v in loads(np_params["ALLOWED_NETWORK_RULE_LIST"]["value"]))
    blocked_network_rule_list = sorted(v["fullyQualifiedRuleName"] for v in loads(np_params["BLOCKED_NETWORK_RULE_LIST"]["value"]))

    assert str(allowed_network_rule_list[0]).endswith("DB1.SC1.NP002_NR1")
    assert str(allowed_network_rule_list[1]).endswith("DB1.SC1.NP002_NR2")
    assert str(blocked_network_rule_list[0]).endswith("DB1.SC1.NP002_NR3")
    assert str(blocked_network_rule_list[1]).endswith("DB1.SC1.NP002_NR4")


def test_step2(helper):
    np = helper.show_network_policy("np002_np1")
    np_params = helper.desc_network_policy("np002_np1")

    assert np["entries_in_allowed_network_rules"] == 1
    assert np["entries_in_allowed_network_rules"] == 1

    allowed_network_rule_list = sorted(v["fullyQualifiedRuleName"] for v in loads(np_params["ALLOWED_NETWORK_RULE_LIST"]["value"]))
    blocked_network_rule_list = sorted(v["fullyQualifiedRuleName"] for v in loads(np_params["BLOCKED_NETWORK_RULE_LIST"]["value"]))

    assert str(allowed_network_rule_list[0]).endswith("DB1.SC1.NP002_NR1")
    assert str(blocked_network_rule_list[0]).endswith("DB1.SC1.NP002_NR3")


def test_step3(helper):
    np = helper.show_network_policy("np002_np1")

    assert np is None
