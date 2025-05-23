from snowddl.blueprint import BaseDataType


def test_step1(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr001_pr1")
    procedure_dtypes = helper.dtypes_from_arguments(procedure_show["arguments"])

    procedure_desc = helper.desc_procedure("db1", "sc1", "pr001_pr1", procedure_dtypes)

    # Compare data types of arguments
    assert procedure_dtypes == [
        BaseDataType.NUMBER,
        BaseDataType.NUMBER,
        BaseDataType.NUMBER,
        BaseDataType.NUMBER,
        BaseDataType.FLOAT,
        BaseDataType.BINARY,
        BaseDataType.BINARY,
        BaseDataType.VARCHAR,
        BaseDataType.VARCHAR,
        BaseDataType.DATE,
        BaseDataType.TIME,
        BaseDataType.TIME,
        BaseDataType.TIMESTAMP_LTZ,
        BaseDataType.TIMESTAMP_LTZ,
        BaseDataType.TIMESTAMP_NTZ,
        BaseDataType.TIMESTAMP_NTZ,
        BaseDataType.TIMESTAMP_TZ,
        BaseDataType.TIMESTAMP_TZ,
        BaseDataType.VARIANT,
        BaseDataType.OBJECT,
        BaseDataType.ARRAY,
        BaseDataType.GEOGRAPHY,
        BaseDataType.GEOMETRY,
    ]

    # Compare returns signature
    # This check is muted due to upcoming: https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_03/bcr-1944
    """
    assert (
        procedure_desc["returns"] == "TABLE ("
        "NUM1 NUMBER, NUM2 NUMBER, NUM3 NUMBER, NUM4 NUMBER, "
        "DBL FLOAT, "
        "BIN1 BINARY, BIN2 BINARY, "
        "VAR1 VARCHAR, VAR2 VARCHAR, "
        "DT1 DATE, "
        "TM1 TIME, TM2 TIME, "
        "LTZ1 TIMESTAMP_LTZ, LTZ2 TIMESTAMP_LTZ, "
        "NTZ1 TIMESTAMP_NTZ, NTZ2 TIMESTAMP_NTZ, "
        "TZ1 TIMESTAMP_TZ, TZ2 TIMESTAMP_TZ, "
        "VAR VARIANT, "
        "OBJ OBJECT, "
        "ARR ARRAY, "
        "GEO1 GEOGRAPHY, "
        "GEO2 GEOMETRY)"
    )
    """

    assert procedure_desc["language"] == "SQL"
    assert procedure_desc["execute as"] == "OWNER"

    # Validate fact that short hash is present
    assert procedure_show["description"].startswith("abc #")


def test_step2(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr001_pr1")
    procedure_dtypes = helper.dtypes_from_arguments(procedure_show["arguments"])

    procedure_desc = helper.desc_procedure("db1", "sc1", "pr001_pr1", procedure_dtypes)

    # Compare data types of arguments
    assert procedure_dtypes == [
        BaseDataType.NUMBER,
        BaseDataType.NUMBER,
        BaseDataType.NUMBER,
        BaseDataType.FLOAT,
        BaseDataType.BINARY,
        BaseDataType.VARCHAR,
        BaseDataType.DATE,
        BaseDataType.TIME,
        BaseDataType.TIMESTAMP_LTZ,
        BaseDataType.TIMESTAMP_NTZ,
        BaseDataType.TIMESTAMP_TZ,
        BaseDataType.VARIANT,
        BaseDataType.OBJECT,
        BaseDataType.ARRAY,
        BaseDataType.GEOGRAPHY,
        BaseDataType.GEOMETRY,
    ]

    # Compare returns signature
    # This check is muted due to upcoming: https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_03/bcr-1944
    """
    assert (
        procedure_desc["returns"] == "TABLE ("
        "NUM1 NUMBER, NUM2 NUMBER, NUM3 NUMBER, "
        "DBL FLOAT, "
        "BIN1 BINARY, "
        "VAR1 VARCHAR, "
        "DT1 DATE, "
        "TM1 TIME, "
        "LTZ1 TIMESTAMP_LTZ, "
        "NTZ1 TIMESTAMP_NTZ, "
        "TZ1 TIMESTAMP_TZ, "
        "VAR VARIANT, "
        "OBJ OBJECT, "
        "ARR ARRAY, "
        "GEO1 GEOGRAPHY, "
        "GEO2 GEOMETRY)"
    )
    """

    assert procedure_desc["language"] == "SQL"
    assert procedure_desc["execute as"] == "CALLER"

    # Validate fact that short hash is present
    assert procedure_show["description"].startswith("cde #")


def test_step3(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr001_pr1")

    # Table was dropped
    assert procedure_show is None
