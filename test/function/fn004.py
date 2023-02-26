def test_step1(helper):
    function_show = helper.show_function("db1", "sc1", "fn004_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show['arguments'])

    function_desc = helper.desc_function("db1", "sc1", "fn004_fn1", function_dtypes)

    assert function_show['language'] == "PYTHON"
    assert function_show['arguments'] == "FN004_FN1(VARCHAR, NUMBER, NUMBER) RETURN TABLE (SYMBOL VARCHAR, TOTAL NUMBER)"

    assert function_desc['runtime_version'] == "3.8"
    assert function_desc['handler'] == "StockSaleSum"

    assert "StockSaleSum" in function_desc['body']
    assert function_desc['imports'] == "[]"
    assert function_desc['packages'] == "[]"


def test_step2(helper):
    function_show = helper.show_function("db1", "sc1", "fn004_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show['arguments'])

    function_desc = helper.desc_function("db1", "sc1", "fn004_fn1", function_dtypes)

    assert function_show['language'] == "PYTHON"
    assert function_show['arguments'] == "FN004_FN1(VARCHAR, NUMBER, NUMBER) RETURN TABLE (SYMBOL VARCHAR, TOTAL NUMBER)"

    assert function_desc['runtime_version'] == "3.8"
    assert function_desc['handler'] == "fn004_stock.StockSaleSum"

    assert not function_desc['body']
    assert "fn004_stock" in function_desc['imports']

def test_step3(helper):
    function_show = helper.show_function("db1", "sc1", "fn004_fn1")

    assert function_show is None
