from json import loads

from snowddl import AccountObjectIdent, SchemaObjectIdent


def usage_grants(helper):
    cur = helper.execute(
        "SHOW GRANTS TO ROLE {role:i}",
        {"role": AccountObjectIdent(helper.env_prefix, "mcp001_tr1__T_ROLE")},
    )
    return {row["name"].replace('"', "") for row in cur if row["granted_on"] == "MCP_SERVER" and row["privilege"] == "USAGE"}


def test_step1(helper):
    server = helper.desc_mcp_server("db1", "sc1", "mcp001_mcp1")
    tool = loads(server["server_spec"])["tools"][0]
    assert tool["type"] == "SYSTEM_EXECUTE_SQL"
    assert tool["description"] == "SQL execution tool created by SnowDDL."
    assert str(SchemaObjectIdent(helper.env_prefix, "db1", "sc1", "mcp001_mcp1")) in usage_grants(helper)


def test_step2(helper):
    server = helper.desc_mcp_server("db1", "sc1", "mcp001_mcp1")
    assert loads(server["server_spec"])["tools"][0]["description"] == "Updated SQL execution tool."
    assert str(SchemaObjectIdent(helper.env_prefix, "db1", "sc1", "mcp001_mcp1")) in usage_grants(helper)


def test_step3(helper):
    # Empty collections stop management; the final server remains until explicitly dropped or its schema is destroyed.
    assert helper.show_mcp_server("db1", "sc1", "mcp001_mcp1") is not None
    assert not usage_grants(helper)
