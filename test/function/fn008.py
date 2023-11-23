from snowddl.blueprint import BaseDataType


def test_step1(helper):
    function_show = helper.show_function("db1", "sc1", "fn008_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])

    function_desc = helper.desc_function("db1", "sc1", "fn008_fn1", function_dtypes)

    # Compare data types of arguments
    assert function_dtypes == [
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
    assert (
        function_desc["returns"] == "TABLE ("
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
        "ARR ARRAY, "
        "GEO1 GEOGRAPHY, "
        "GEO2 GEOMETRY)"
    )

    assert function_desc["language"] == "SQL"
    assert "[" in function_show["arguments"]


def test_step2(helper):
    function_show = helper.show_function("db1", "sc1", "fn008_fn1")
    function_dtypes = helper.dtypes_from_arguments(function_show["arguments"])

    function_desc = helper.desc_function("db1", "sc1", "fn008_fn1", function_dtypes)

    # Compare data types of arguments
    assert function_dtypes == [
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
    assert (
            function_desc["returns"] == "TABLE ("
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
                                        "ARR ARRAY, "
                                        "GEO1 GEOGRAPHY, "
                                        "GEO2 GEOMETRY)"
    )

    assert function_desc["language"] == "SQL"
    assert "[" in function_show["arguments"]


def test_step3(helper):
    function_show = helper.show_function("db1", "sc1", "fn008_fn1")

    # Table was dropped
    assert function_show is None
