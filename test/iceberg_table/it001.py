import os
import pytest

pytestmark = pytest.mark.skipif(os.environ.get("TEST_LITE"), reason="Tests require additional setup for Iceberg tables")


def test_step1(helper):
    iceberg_table_show = helper.show_iceberg_table("iceberg_db1", "iceberg_sc1", "it001_it1")

    assert iceberg_table_show["iceberg_table_type"] == "UNMANAGED"
    assert iceberg_table_show["external_volume_name"] == "TEST_EXTERNAL_VOLUME_GLUE"
    assert iceberg_table_show["catalog_name"] == "TEST_CATALOG_GLUE"

    assert iceberg_table_show["catalog_table_name"] == "test_iceberg_table_1"
    assert iceberg_table_show["comment"].startswith("abc #")


def test_step2(helper):
    iceberg_table_show = helper.show_iceberg_table("iceberg_db1", "iceberg_sc1", "it001_it1")

    assert iceberg_table_show["iceberg_table_type"] == "UNMANAGED"
    assert iceberg_table_show["external_volume_name"] == "TEST_EXTERNAL_VOLUME_GLUE"
    assert iceberg_table_show["catalog_name"] == "TEST_CATALOG_GLUE"

    assert iceberg_table_show["catalog_table_name"] == "test_iceberg_table_2"
    assert iceberg_table_show["comment"].startswith("cde #")


def test_step3(helper):
    iceberg_table_show = helper.show_iceberg_table("iceberg_db1", "iceberg_sc1", "it001_it1")

    # Table was dropped
    assert iceberg_table_show is None
