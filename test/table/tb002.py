def test_step1(helper):
    table = helper.show_table("db1", "sc1", "tb002_tb1")
    cols = helper.desc_table("db1", "sc1", "tb002_tb1")

    # Empty table comment
    assert not table['comment']

    # Empty column comments
    assert not cols['ID']['comment']
    assert not cols['NAME']['comment']

    # Defaults are set
    assert "TB002_SQ1" in cols['ID']['default']
    assert cols['NAME']['default']

    # Other params are off
    assert not table['cluster_by']
    assert table['change_tracking'] == "OFF"

    if helper.is_edition_enterprise():
        assert table['search_optimization'] == "OFF"


def test_step2(helper):
    table = helper.show_table("db1", "sc1", "tb002_tb1")
    cols = helper.desc_table("db1", "sc1", "tb002_tb1")

    # Set table comment
    assert table['comment']

    # Set column comments
    assert cols['ID']['comment']
    assert cols['NAME']['comment']

    # Default sequence was changed
    assert "TB002_SQ2" in cols['ID']['default']

    # Default value is gone
    assert not cols['NAME']['default']

    # Other params are on
    assert table['cluster_by']
    assert table['change_tracking'] == "ON"

    if helper.is_edition_enterprise():
        assert table['search_optimization'] == "ON"


def test_step3(helper):
    table = helper.show_table("db1", "sc1", "tb002_tb1")
    cols = helper.desc_table("db1", "sc1", "tb002_tb1")

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
