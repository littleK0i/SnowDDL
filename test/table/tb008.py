from snowddl import SchemaObjectIdent


def test_step1(helper):
    pk = helper.show_primary_key("db1", "sc1", "tb008_tb2")
    uk = helper.show_unique_keys("db1", "sc1", "tb008_tb2")
    fk = helper.show_foreign_keys("db1", "sc1", "tb008_tb2")

    assert pk == ["BOOK_ID"]
    assert uk == [["BOOK_ISBN"]]

    assert len(fk) == 1

    assert {
        "columns": ["AUTHOR_ID"],
        "ref_table": str(SchemaObjectIdent(helper.env_prefix, "db1", "sc1", "tb008_tb1")),
        "ref_columns": ["AUTHOR_ID"],
    } in fk


def test_step2(helper):
    pk = helper.show_primary_key("db1", "sc1", "tb008_tb2")
    uk = helper.show_unique_keys("db1", "sc1", "tb008_tb2")
    fk = helper.show_foreign_keys("db1", "sc1", "tb008_tb2")

    assert pk == ["BOOK_ID"]
    assert uk == [["BOOK_ISBN"]]

    assert len(fk) == 1

    assert {
        "columns": ["AUTHOR_ID"],
        "ref_table": str(SchemaObjectIdent(helper.env_prefix, "db1", "sc1", "tb008_tb1")),
        "ref_columns": ["AUTHOR_ID"],
    } in fk


def test_step3(helper):
    pk = helper.show_primary_key("db1", "sc1", "tb008_tb2")
    uk = helper.show_unique_keys("db1", "sc1", "tb008_tb2")
    fk = helper.show_foreign_keys("db1", "sc1", "tb008_tb2")

    assert pk == []
    assert uk == []
    assert fk == []
