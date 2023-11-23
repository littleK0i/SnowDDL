from snowddl.blueprint import BaseDataType


def test_step1(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr004_pr1")
    procedure_dtypes = helper.dtypes_from_arguments(procedure_show["arguments"])

    procedure_desc = helper.desc_procedure("db1", "sc1", "pr004_pr1", procedure_dtypes)

    # Compare data types of arguments
    assert procedure_dtypes == [
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
    ]

    # Compare returns signature
    assert (
        procedure_desc["returns"] == "TABLE ("
        "NUM1 NUMBER, NUM2 NUMBER, "
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
        "ARR ARRAY)"
    )

    assert "[" in procedure_show["arguments"]


def test_step2(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr004_pr1")
    procedure_dtypes = helper.dtypes_from_arguments(procedure_show["arguments"])

    procedure_desc = helper.desc_procedure("db1", "sc1", "pr004_pr1", procedure_dtypes)

    # Compare data types of arguments
    assert procedure_dtypes == [
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
    ]

    # Compare returns signature
    assert (
        procedure_desc["returns"] == "TABLE ("
        "NUM1 NUMBER, NUM2 NUMBER, "
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
        "ARR ARRAY)"
    )

    assert "[" in procedure_show["arguments"]


def test_step3(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr004_pr1")

    # Table was dropped
    assert procedure_show is None
