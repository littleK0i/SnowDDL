from snowddl.blueprint import BaseDataType


def test_step1(helper):
    function_show = helper.show_function("db1", "sc1", "fn011_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])

    assert function_dtypes == [BaseDataType.VARCHAR]
    assert function_show["language"] == "JAVASCRIPT"
    assert function_show["description"].startswith("abc #")


def test_step2(helper):
    function_show = helper.show_function("db1", "sc1", "fn011_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])

    assert function_dtypes == [BaseDataType.VARCHAR, BaseDataType.VARCHAR]
    assert function_show["description"].startswith("cde #")


def test_step3(helper):
    function_show = helper.show_function("db1", "sc1", "fn011_fn1")

    assert function_show is None
