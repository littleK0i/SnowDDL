from snowddl.blueprint import BaseDataType


def test_step1(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr005_pr1")
    procedure_dtypes = helper.dtypes_from_arguments(procedure_show["arguments"])

    procedure_desc = helper.desc_procedure("db1", "sc1", "pr005_pr1", procedure_dtypes)

    assert procedure_dtypes == [BaseDataType.VARCHAR]
    assert procedure_desc["language"] == "JAVASCRIPT"
    assert procedure_show["description"].startswith("abc #")


def test_step2(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr005_pr1")
    procedure_dtypes = helper.dtypes_from_arguments(procedure_show["arguments"])

    assert procedure_dtypes == [BaseDataType.VARCHAR, BaseDataType.VARCHAR]
    assert procedure_show["description"].startswith("cde #")


def test_step3(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr005_pr1")

    assert procedure_show is None
