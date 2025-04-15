def test_step1(helper):
    function_show = helper.show_function("db1", "sc1", "fn010_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])
    function_desc = helper.desc_function("db1", "sc1", "fn010_fn1", function_dtypes)

    assert function_desc["language"] == "PYTHON"
    assert function_desc["is_aggregate"] == "true"
    assert function_desc["handler"] == "PythonSum"
    assert function_desc["signature"] == "(A NUMBER)"
    assert function_desc["returns"] == "NUMBER(38,0)"


def test_step2(helper):
    function_show = helper.show_function("db1", "sc1", "fn010_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])
    function_desc = helper.desc_function("db1", "sc1", "fn010_fn1", function_dtypes)

    assert function_desc["language"] == "PYTHON"
    assert function_desc["is_aggregate"] == "true"
    assert function_desc["handler"] == "PythonGetUniqueValues"
    assert function_desc["signature"] == "(INPUT ARRAY)"
    assert function_desc["returns"] == "ARRAY"


def test_step3(helper):
    function_show = helper.show_function("db1", "sc1", "fn010_fn1")

    assert function_show is None
