def test_step1(helper):
    show = helper.show_network_rule("db1", "sc1", "nr001_nr1")
    desc = helper.desc_network_rule("db1", "sc1", "nr001_nr1")

    assert show["type"] == "IPV4"
    assert show["mode"] == "INGRESS"
    assert show["comment"] == "abc"

    assert desc["value_list"].split(",") == ["192.168.2.0/24", "192.168.1.99"]


def test_step2(helper):
    show = helper.show_network_rule("db1", "sc1", "nr001_nr1")
    desc = helper.desc_network_rule("db1", "sc1", "nr001_nr1")

    assert show["type"] == "IPV4"
    assert show["mode"] == "INGRESS"
    assert show["comment"] == "cde"

    assert desc["value_list"].split(",") == ["192.168.2.0/23", "192.168.1.100"]


def test_step3(helper):
    show = helper.show_network_rule("db1", "sc1", "nr001_nr1")

    assert show is None
