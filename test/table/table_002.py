def test_002_step1(helper):
    table = helper.show_table("db1", "sc1", "table_002")
    cols = helper.desc_table("db1", "sc1", "table_002")

    # Empty table comment
    assert not table['comment']

    # Empty column comments
    assert not cols['ID']['comment']
    assert not cols['NAME']['comment']

    # Defaults are set
    assert "SEQUENCE_002_01" in cols['ID']['default']
    assert cols['NAME']['default']

    # Other params are off
    assert not table['cluster_by']
    assert table['change_tracking'] == "OFF"

    if helper.is_edition_enterprise():
        assert table['search_optimization'] == "OFF"


def test_002_step2(helper):
    table = helper.show_table("db1", "sc1", "table_002")
    cols = helper.desc_table("db1", "sc1", "table_002")

    # Set table comment
    assert table['comment']

    # Set column comments
    assert cols['ID']['comment']
    assert cols['NAME']['comment']

    # Default sequence was changed
    assert "SEQUENCE_002_02" in cols['ID']['default']

    # Default value is gone
    assert not cols['NAME']['default']

    # Other params are on
    assert table['cluster_by']
    assert table['change_tracking'] == "ON"

    if helper.is_edition_enterprise():
        assert table['search_optimization'] == "ON"


def test_002_step3(helper):
    table = helper.show_table("db1", "sc1", "table_002")
    cols = helper.desc_table("db1", "sc1", "table_002")


    # Empty table comment
    assert not table['comment']

    # Empty column comments
    assert not cols['ID']['comment']
    assert not cols['NAME']['comment']

    # Defaults are empty again
    assert not cols['ID']['default']
    assert not cols['NAME']['default']

    # Other params are off again
    assert not table['cluster_by']
    assert table['change_tracking'] == "OFF"

    if helper.is_edition_enterprise():
        assert table['search_optimization'] == "OFF"
