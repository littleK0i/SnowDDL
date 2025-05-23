def test_step1(helper):
    function_show = helper.show_function("db1", "sc1", "fn007_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])

    function_desc = helper.desc_function("db1", "sc1", "fn007_fn1", function_dtypes)

    assert function_show["language"] == "JAVASCRIPT"
    assert function_show["arguments"] == "FN007_FN1(FLOAT) RETURN FLOAT"

    assert function_desc["body"]


def test_step2(helper):
    function_show = helper.show_function("db1", "sc1", "fn007_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])

    function_desc = helper.desc_function("db1", "sc1", "fn007_fn1", function_dtypes)

    assert function_show["language"] == "JAVASCRIPT"
    # assert function_show["arguments"] == "FN007_FN1() RETURN TABLE (OUTPUT_COL VARCHAR)"

    assert function_desc["body"]


def test_step3(helper):
    function_show = helper.show_function("db1", "sc1", "fn007_fn1")

    assert function_show is None
