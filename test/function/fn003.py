def test_step1(helper):
    function_show = helper.show_function("db1", "sc1", "fn003_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])

    function_desc = helper.desc_function("db1", "sc1", "fn003_fn1", function_dtypes)

    assert function_show["language"] == "PYTHON"
    assert function_show["arguments"] == "FN003_FN1(NUMBER) RETURN NUMBER"

    assert function_desc["runtime_version"] == "3.11"
    assert function_desc["handler"] == "addone_py"

    assert "addone_py" in function_desc["body"]
    assert function_desc["imports"] == "[]"
    assert function_desc["packages"] == "[]"


def test_step2(helper):
    function_show = helper.show_function("db1", "sc1", "fn003_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])

    function_desc = helper.desc_function("db1", "sc1", "fn003_fn1", function_dtypes)

    assert function_show["language"] == "PYTHON"
    assert function_show["arguments"] == "FN003_FN1(NUMBER) RETURN NUMBER"

    assert function_desc["runtime_version"] == "3.11"
    assert function_desc["handler"] == "fn003_addone.addone_py"

    assert not function_desc["body"]
    assert "fn003_addone" in function_desc["imports"]

    assert "numpy" in function_desc["packages"]
    assert "pandas" in function_desc["packages"]


def test_step3(helper):
    function_show = helper.show_function("db1", "sc1", "fn003_fn1")

    assert function_show is None
