# fn012_fn2 calls fn012_fn1 in its body, and declares it via "depends_on".
# Snowflake binds function bodies at CREATE time, so fn012_fn1 must exist
# before fn012_fn2 is created, or CREATE FUNCTION fails with "does not exist".
# Without "depends_on" both functions land in the same resolver batch and
# are created concurrently, racing on which one Snowflake sees first.


def test_step1(helper):
    function_1_show = helper.show_function("db1", "sc1", "fn012_fn1")
    function_2_show = helper.show_function("db1", "sc1", "fn012_fn2")

    assert function_1_show
    assert function_2_show


def test_step3(helper):
    function_1_show = helper.show_function("db1", "sc1", "fn012_fn1")
    function_2_show = helper.show_function("db1", "sc1", "fn012_fn2")

    assert function_1_show is None
    assert function_2_show is None
