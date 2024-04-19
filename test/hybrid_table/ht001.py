def test_step1(helper):
    hybrid_table_show = helper.show_hybrid_table("db1", "sc1", "ht001_ht1")
    indexes = helper.show_indexes("db1", "sc1", "ht001_ht1")

    primary_key = helper.show_primary_key("db1", "sc1", "ht001_ht1")
    unique_keys = helper.show_unique_keys("db1", "sc1", "ht001_ht1")
    foreign_keys = helper.show_foreign_keys("db1", "sc1", "ht001_ht1")

    assert 1 == len(primary_key)
    assert ["NUM1"] == primary_key

    assert 2 == len(unique_keys)
    assert ["NUM2"] in unique_keys
    assert ["NUM3", "NUM4", "VAR1", "VAR2"] in unique_keys

    assert 2 == len(foreign_keys)
    assert {"columns": ["NUM2"], "ref_table": f"{helper.env_prefix}DB1.SC1.HT001_HT2", "ref_columns": ["ID"]} in foreign_keys
    assert {"columns": ["VAR1", "VAR2"], "ref_table": f"{helper.env_prefix}DB1.SC1.HT001_HT2", "ref_columns": ["FIRST_NAME", "LAST_NAME"]} in foreign_keys

    assert "SYS_INDEX_HT001_HT1_PRIMARY" in indexes
    assert "SYS_INDEX_HT001_HT1_UNIQUE_NUM2" in indexes
    assert "SYS_INDEX_HT001_HT1_UNIQUE_NUM3_NUM4_VAR1_VAR2" in indexes
    assert "SYS_INDEX_HT001_HT1_FOREIGN_KEY_VAR1_VAR2_HT001_HT2_FIRST_NAME_LAST_NAME" in indexes
    assert "SYS_INDEX_HT001_HT1_FOREIGN_KEY_NUM2_HT001_HT2_ID" in indexes
    assert "INDEX__NUM2" in indexes
    assert "INDEX__NUM2__NUM3" in indexes
    assert "INDEX__NUM2__NUM3" in indexes

    assert hybrid_table_show["comment"].startswith("abc #")


def test_step2(helper):
    # Make sure foreign key was correctly re-established after "ht001_ht2" was re-created
    # and implicitly dropped foreign keys on "ht001_ht1"
    foreign_keys = helper.show_foreign_keys("db1", "sc1", "ht001_ht1")

    # TODO: uncomment these checks when Snowflake fixes foreign keys for Hybrid Tables
    # As of 19 Apr 2024, it is no longer possible to add foreign key to existing Hybrid Table

    #assert 2 == len(foreign_keys)
    #assert {"columns": ["NUM2"], "ref_table": f"{helper.env_prefix}DB1.SC1.HT001_HT2", "ref_columns": ["ID"]} in foreign_keys
    #assert {"columns": ["VAR1", "VAR2"], "ref_table": f"{helper.env_prefix}DB1.SC1.HT001_HT2", "ref_columns": ["FIRST_NAME", "LAST_NAME"]} in foreign_keys


def test_step3(helper):
    hybrid_table_show = helper.show_hybrid_table("db1", "sc1", "ht001_ht1")

    # Table was dropped
    assert hybrid_table_show is None
