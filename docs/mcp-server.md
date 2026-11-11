# MCP servers

Declare Snowflake-managed MCP servers in `<database>/<schema>/mcp_server.yaml`. Each mapping key is a server name;
the directory path supplies the database and schema. Multiple servers can share one file, and the same server name
can be used in different schemas.

For example, `SAMPLE_DB/RAW/mcp_server.yaml`:

```yaml
SAMPLE_MCP:
  tools:
    - name: sql_exec_tool
      type: SYSTEM_EXECUTE_SQL
      title: SAMPLE_DB SQL Execution
      description: >-
        Executes SQL using the caller's permissions.
        Use fully qualified names: SAMPLE_DB.<SCHEMA>.<OBJECT>.
```

Merge the following grant into an existing technical role's `grants` mapping in root `technical_role.yaml`:

```yaml
git a
```

The technical role follows normal SnowDDL naming, including its environment prefix and `__T_ROLE` suffix.
The caller still needs its existing database/schema, underlying object, and warehouse permissions. A tool description
does not restrict SQL access. User, role, warehouse, and client authentication provisioning are separate workflows.

## Tools

Every tool requires `name`, `type`, `title`, and `description`. Names must be unique within the server, which supports
1–50 tools. Supported types are:

| Type | Additional fields |
| --- | --- |
| `SYSTEM_EXECUTE_SQL` | None. Uses the caller's existing execution context. |
| `CORTEX_SEARCH_SERVICE_QUERY` | `identifier` naming the search service. |
| `CORTEX_ANALYST_MESSAGE` | `identifier` naming the semantic view. |
| `CORTEX_AGENT_RUN` | `identifier` naming the agent; optional `annotations`. |
| `GENERIC` | `identifier`, `config.type`, `config.warehouse`, `config.input_schema`; optional `annotations`. |
| `CODING_AGENT` | Optional native agent `config`; no `identifier`. |

Referenced Cortex objects can be provisioned outside SnowDDL. Generic tools use `config.type: function` or `procedure`.
The following server exposes a procedure:

```yaml
CALCULATIONS_MCP:
  tools:
    - name: calculate
      type: GENERIC
      title: Calculate
      description: Calls the existing calculation procedure.
      identifier: CALCULATE_VALUES
      annotations:
        readOnlyHint: true
      config:
        type: procedure
        warehouse: COMPUTE
        input_schema:
          type: object
          properties:
            value:
              type: number
          required: [value]
```

Object references accept `object`, `schema.object`, or `database.schema.object`, following SnowDDL's identifier
conventions. The environment prefix is applied to database and warehouse identifiers. Single-database mode remaps
typed database references to the target database, following its existing behavior. Tool names, descriptions,
instructions, and JSON Schema property names retain their original case and content. Placeholders work inside tool
mappings and nested configuration.

The supported annotation keys are `readOnlyHint`, `destructiveHint`, `idempotentHint`, and `openWorldHint`; values are
booleans. They are client hints and do not enforce access control. Coding-agent `config` must omit runtime request
fields: `messages`, `thread_id`, `parent_message_id`, `stream`, `background`, and `origin_application`.

See Snowflake's [MCP server guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp) and
[CREATE MCP SERVER reference](https://docs.snowflake.com/en/sql-reference/sql/create-mcp-server) for tool behavior and
the underlying privileges required to invoke each tool.

## Reconciliation

SnowDDL creates missing servers and compares existing `DESCRIBE MCP SERVER.server_spec` content with the desired
definition. Tool ordering, mapping ordering, the native specification version marker, and documented annotation
defaults do not cause replacements. A changed definition uses `CREATE OR REPLACE MCP SERVER` and requires
`--apply-unsafe`. Identifiers and the serialized specification use SnowDDL's SQL formatter for quoting.

The MCP resolver runs before technical-role reconciliation, allowing configured usage grants to be restored after a
replacement in the same apply. Grants maintained outside SnowDDL are not guaranteed to survive replacement.
Server-level `comment` is not supported.

Only schemas with at least one declared MCP server are managed. Unconfigured servers in those schemas are scheduled
for removal, except in sandbox schemas; removal requires `--apply-unsafe`. Removing the final declaration from a schema,
including making its collection `{}` or deleting its file, stops management of that schema's servers and does not
drop them. To remove every server, use an explicit reviewed `DROP MCP SERVER` operation or the normal parent-schema
destruction workflow.

## Validation

MCP tests follow the object-type directory and numbered case-file convention in `test/mcp_server/`.
`mcp001.py` checks the live three-step lifecycle; `mcp002.py` contains offline configuration and reconciliation
checks named `test_step1_*`. Both `test/run_test_full.sh` and `test/run_test_lite.sh` collect `*/*.py` from `test/`
and select tests by step, so the offline cases run once during step 1 through the existing runners.

Run those offline checks directly with `python -m pytest -q test/mcp_server/mcp002.py`.
The full and lite scripts apply and destroy isolated Snowflake test resources and require an appropriate test account;
offline tests do not establish Snowflake DDL or MCP client compatibility.
