from snowddl.blueprint import BaseDataType


def test_step1(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr002_pr1")
    procedure_dtypes = helper.dtypes_from_arguments(procedure_show['arguments'])

    procedure_desc = helper.desc_procedure("db1", "sc1", "pr002_pr1", procedure_dtypes)

    # Compare data types of arguments
    assert procedure_dtypes == []

    # Compare returns signature
    assert procedure_desc['returns'] == "VARCHAR(10)"

    assert procedure_desc['language'] == "JAVASCRIPT"
    assert procedure_desc['execute as'] == "OWNER"

    # Validate fact that short hash is present
    assert procedure_show['description'].startswith("abc #")


def test_step2(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr002_pr1")
    procedure_dtypes = helper.dtypes_from_arguments(procedure_show['arguments'])

    procedure_desc = helper.desc_procedure("db1", "sc1", "pr002_pr1", procedure_dtypes)

    # Compare data types of arguments
    assert procedure_dtypes == [BaseDataType.VARCHAR]

    # Compare returns signature
    assert procedure_desc['returns'] == "VARCHAR(10)"

    assert procedure_desc['language'] == "JAVASCRIPT"
    assert procedure_desc['execute as'] == "OWNER"

    # Validate fact that short hash is present
    assert procedure_show['description'].startswith("cde #")


def test_step3(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr002_pr1")
    procedure_dtypes = helper.dtypes_from_arguments(procedure_show['arguments'])

    procedure_desc = helper.desc_procedure("db1", "sc1", "pr002_pr1", procedure_dtypes)

    # Compare data types of arguments
    assert procedure_dtypes == [BaseDataType.VARCHAR]

    # Compare returns signature
    assert procedure_desc['returns'] == "VARCHAR(100)"

    assert procedure_desc['language'] == "JAVASCRIPT"
    assert procedure_desc['execute as'] == "OWNER"

    # Validate fact that short hash is present
    assert procedure_show['description'].startswith("#")
