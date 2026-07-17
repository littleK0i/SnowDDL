def test_step1(helper):
    grants = helper.show_grants_to_role("tr001_tr1__T_ROLE")

    assert any(
        g["privilege"] == "USAGE" and g["granted_on"] == "DATABASE_ROLE" and g["name"] == "SNOWFLAKE.CORTEX_USER" for g in grants
    )


def test_step2(helper):
    grants = helper.show_grants_to_role("tr001_tr1__T_ROLE")

    assert any(
        g["privilege"] == "USAGE" and g["granted_on"] == "DATABASE_ROLE" and g["name"] == "SNOWFLAKE.CORTEX_USER" for g in grants
    )


def test_step3(helper):
    assert helper.show_role("tr001_tr1__T_ROLE") is None
