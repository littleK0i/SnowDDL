def test_step1(helper):
    m = helper.show_resource_monitor("rm001_rm1")

    assert m["credit_quota"] == "100.00"
    assert m["frequency"] == "MONTHLY"
    assert m["notify_at"] == "50%,75%"
    assert m["suspend_at"] == "100%"
    assert m["suspend_immediately_at"] == "110%"


def test_step2(helper):
    m = helper.show_resource_monitor("rm001_rm1")

    assert m["credit_quota"] == "50.00"
    assert m["frequency"] == "DAILY"
    assert m["notify_at"] == "20%,60%"
    assert m["suspend_at"] == "90%"
    assert m["suspend_immediately_at"] == "100%"


def test_step3(helper):
    m = helper.show_resource_monitor("rm001_rm1")

    assert m is None
