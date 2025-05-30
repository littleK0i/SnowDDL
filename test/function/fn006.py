def test_step1(helper):
    function_show = helper.show_function("db1", "sc1", "fn006_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])

    function_desc = helper.desc_function("db1", "sc1", "fn006_fn1", function_dtypes)

    assert function_show["language"] == "JAVA"
    # assert function_show["arguments"] == "FN006_FN1(VARCHAR) RETURN TABLE (OUTPUT_VALUE VARCHAR)"

    assert function_desc["runtime_version"] == "11"
    assert function_desc["handler"] == "TestFunction"

    assert "TestFunction" in function_desc["body"]
    assert function_desc["imports"] == "[]"
    assert function_desc["packages"] == "[]"


def test_step2(helper):
    # TODO: implement JAR-file checks when possible
    pass


def test_step3(helper):
    function_show = helper.show_function("db1", "sc1", "fn006_fn1")

    assert function_show is None
