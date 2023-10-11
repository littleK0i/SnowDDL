def test_step1(helper):
    table = helper.show_table("db1", "sc1", "tb006_tb1")
    so_items = helper.desc_search_optimization("db1", "sc1", "tb006_tb1")

    # Search optimization is ON
    assert table["search_optimization"] == "ON"

    # Specific search optimization items
    assert {"method": "EQUALITY", "target": "NUM1"} in so_items
    assert {"method": "EQUALITY", "target": "NUM2"} in so_items
    assert {"method": "EQUALITY", "target": "NUM3"} in so_items
    assert {"method": "EQUALITY", "target": "NUM4"} in so_items

    assert {"method": "EQUALITY", "target": "DBL"} not in so_items

    assert {"method": "EQUALITY", "target": "BIN1"} in so_items
    assert {"method": "EQUALITY", "target": "BIN2"} not in so_items

    assert {"method": "EQUALITY", "target": "VAR1"} in so_items
    assert {"method": "EQUALITY", "target": "VAR2"} not in so_items

    assert {"method": "EQUALITY", "target": "DT1"} in so_items
    assert {"method": "EQUALITY", "target": "TM1"} in so_items
    assert {"method": "EQUALITY", "target": "LTZ1"} in so_items
    assert {"method": "EQUALITY", "target": "NTZ1"} in so_items
    assert {"method": "EQUALITY", "target": "TZ1"} in so_items

    assert {"method": "EQUALITY", "target": "VAR"} in so_items
    assert {"method": "EQUALITY", "target": "OBJ"} in so_items
    assert {"method": "EQUALITY", "target": "ARR"} in so_items

    assert {"method": "GEO", "target": "GEO1"} in so_items
    assert {"method": "GEO", "target": "GEO2"} not in so_items


def test_step2(helper):
    table = helper.show_table("db1", "sc1", "tb006_tb1")
    so_items = helper.desc_search_optimization("db1", "sc1", "tb006_tb1")

    # Search optimization is ON
    assert table["search_optimization"] == "ON"

    # Specific search optimization items
    assert {"method": "EQUALITY", "target": "NUM1"} in so_items
    assert {"method": "EQUALITY", "target": "NUM2"} not in so_items
    assert {"method": "EQUALITY", "target": "NUM3"} not in so_items
    assert {"method": "EQUALITY", "target": "NUM4"} in so_items

    assert {"method": "EQUALITY", "target": "BIN1"} not in so_items
    assert {"method": "EQUALITY", "target": "BIN2"} in so_items

    assert {"method": "EQUALITY", "target": "VAR1"} not in so_items
    assert {"method": "EQUALITY", "target": "VAR2"} in so_items

    assert {"method": "GEO", "target": "GEO1"} not in so_items
    assert {"method": "GEO", "target": "GEO2"} not in so_items


def test_step3(helper):
    table = helper.show_table("db1", "sc1", "tb006_tb1")
    so_items = helper.desc_search_optimization("db1", "sc1", "tb006_tb1")

    # Search optimization is OFF
    assert table["search_optimization"] == "OFF"

    assert len(so_items) == 0
