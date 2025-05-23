def test_step1(helper):
    function_show = helper.show_function("db1", "sc1", "fn001_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])

    function_desc = helper.desc_function("db1", "sc1", "fn001_fn1", function_dtypes)

    assert function_show["language"] == "SQL"
    # assert function_show["arguments"] == "FN001_FN1() RETURN NUMBER"

    assert function_show["is_table_function"] == "N"
    assert function_show["is_secure"] == "N"
    assert function_show["is_memoizable"] == "N"

    assert function_desc["body"] == "123"

    assert function_show["description"].startswith("abc #")


def test_step2(helper):
    function_show = helper.show_function("db1", "sc1", "fn001_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])

    function_desc = helper.desc_function("db1", "sc1", "fn001_fn1", function_dtypes)

    assert function_show["language"] == "SQL"
    # assert function_show["arguments"] == "FN001_FN1() RETURN VARCHAR"

    assert function_show["is_table_function"] == "N"
    assert function_show["is_secure"] == "Y"
    assert function_show["is_memoizable"] == "Y"

    assert function_desc["body"] == "'abc'"

    assert function_show["description"].startswith("cde #")


def test_step3(helper):
    function_show = helper.show_function("db1", "sc1", "fn001_fn1")

    assert function_show is None
