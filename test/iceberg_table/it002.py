import os
import pytest

pytestmark = pytest.mark.skipif(os.environ.get("TEST_LITE"), reason="Tests require additional setup for Iceberg tables")


def test_step1(helper):
    iceberg_table_show = helper.show_iceberg_table("iceberg_db1", "iceberg_sc2", "it002_it1")

    assert iceberg_table_show["iceberg_table_type"] == "UNMANAGED"
    assert iceberg_table_show["external_volume_name"] == "TEST_EXTERNAL_VOLUME_GLUE"
    assert iceberg_table_show["catalog_name"] == "TEST_CATALOG_OBJECT_STORE"

    assert iceberg_table_show["catalog_table_name"] is None
    assert iceberg_table_show["comment"].startswith("#")


def test_step2(helper):
    iceberg_table_show = helper.show_iceberg_table("iceberg_db1", "iceberg_sc2", "it002_it1")

    assert iceberg_table_show["iceberg_table_type"] == "UNMANAGED"
    assert iceberg_table_show["external_volume_name"] == "TEST_EXTERNAL_VOLUME_GLUE"
    assert iceberg_table_show["catalog_name"] == "TEST_CATALOG_OBJECT_STORE"

    assert iceberg_table_show["catalog_table_name"] is None
    assert iceberg_table_show["comment"].startswith("#")


def test_step3(helper):
    iceberg_table_show = helper.show_iceberg_table("iceberg_db1", "iceberg_sc2", "it002_it1")

    # Table was dropped
    assert iceberg_table_show is None
