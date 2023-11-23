def test_step1(helper):
    show = helper.show_network_rule("db1", "sc1", "nr002_nr1")
    desc = helper.desc_network_rule("db1", "sc1", "nr002_nr1")

    assert show["type"] == "HOST_PORT"
    assert show["mode"] == "EGRESS"

    assert desc["value_list"].split(",") == ["example.com", "company.com:443"]


def test_step2(helper):
    show = helper.show_network_rule("db1", "sc1", "nr002_nr1")
    desc = helper.desc_network_rule("db1", "sc1", "nr002_nr1")

    assert show["type"] == "HOST_PORT"
    assert show["mode"] == "EGRESS"

    assert desc["value_list"].split(",") == ["example.com:80", "microsoft.com:443"]


def test_step3(helper):
    show = helper.show_network_rule("db1", "sc1", "nr002_nr1")

    assert show is None
