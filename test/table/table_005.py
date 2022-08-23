from snowddl import SchemaObjectIdent


def test_005_step1(helper):
    pk = helper.show_primary_key("db1", "sc1", "table_005_02")
    uk = helper.show_unique_keys("db1", "sc1", "table_005_02")
    fk = helper.show_foreign_keys("db1", "sc1", "table_005_02")

    assert pk == ["BOOK_ID"]
    assert uk == [["BOOK_ISBN"]]

    assert len(fk) == 1

    assert {
        "columns": ["AUTHOR_ID"],
        "ref_table": str(SchemaObjectIdent(helper.env_prefix, "db1", "sc1", "table_005_01")),
        "ref_columns": ["AUTHOR_ID"],
    } in fk


def test_005_step2(helper):
    pk = helper.show_primary_key("db1", "sc1", "table_005_02")
    uk = helper.show_unique_keys("db1", "sc1", "table_005_02")
    fk = helper.show_foreign_keys("db1", "sc1", "table_005_02")

    assert pk == ["STORE_ID", "BOOK_ID"]
    assert uk == [["STORE_ID", "BOOK_ISBN"]]

    assert len(fk) == 2

    assert {
        "columns": ["AUTHOR_ID"],
        "ref_table": str(SchemaObjectIdent(helper.env_prefix, "db1", "sc1", "table_005_01")),
        "ref_columns": ["AUTHOR_ID"],
    } in fk

    assert {
        "columns": ["STORE_ID"],
        "ref_table": str(SchemaObjectIdent(helper.env_prefix, "db1", "sc1", "table_005_03")),
        "ref_columns": ["STORE_ID"],
    } in fk


def test_005_step3(helper):
    pk = helper.show_primary_key("db1", "sc1", "table_005_02")
    uk = helper.show_unique_keys("db1", "sc1", "table_005_02")
    fk = helper.show_foreign_keys("db1", "sc1", "table_005_02")

    assert pk == []
    assert uk == []
    assert fk == []
