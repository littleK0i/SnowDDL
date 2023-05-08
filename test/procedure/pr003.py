def test_step1(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr003_pr1")
    procedure_dtypes = helper.dtypes_from_arguments(procedure_show['arguments'])

    procedure_desc = helper.desc_procedure("db1", "sc1", "pr003_pr1", procedure_dtypes)

    assert procedure_desc['language'] == "SQL"


def test_step2(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr003_pr1")
    procedure_dtypes = helper.dtypes_from_arguments(procedure_show['arguments'])

    procedure_desc = helper.desc_procedure("db1", "sc1", "pr003_pr1", procedure_dtypes)

    assert procedure_desc['language'] == "PYTHON"


def test_step3(helper):
    procedure_show = helper.show_procedure("db1", "sc1", "pr003_pr1")
    procedure_dtypes = helper.dtypes_from_arguments(procedure_show['arguments'])

    procedure_desc = helper.desc_procedure("db1", "sc1", "pr003_pr1", procedure_dtypes)

    assert procedure_desc['language'] == "JAVA"
