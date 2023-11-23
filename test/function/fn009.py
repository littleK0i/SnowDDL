def test_step1(helper):
    function_show = helper.show_function("db1", "sc1", "fn009_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])
    function_desc = helper.desc_function("db1", "sc1", "fn009_fn1", function_dtypes)

    assert function_desc["language"] == "PYTHON"

    assert "FN009_EAI1" in function_desc["external_access_integrations"]
    assert "FN009_SE1" in function_desc["secrets"]
    assert "FN009_SE2" in function_desc["secrets"]


def test_step2(helper):
    function_show = helper.show_function("db1", "sc1", "fn009_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])
    function_desc = helper.desc_function("db1", "sc1", "fn009_fn1", function_dtypes)

    assert function_desc["language"] == "PYTHON"

    assert "FN009_EAI1" in function_desc["external_access_integrations"]
    assert "FN009_SE1" in function_desc["secrets"]
    assert "FN009_SE2" not in function_desc["secrets"]


def test_step3(helper):
    function_show = helper.show_function("db1", "sc1", "fn009_fn1")

    assert function_show is None
