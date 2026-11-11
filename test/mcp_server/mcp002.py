from copy import deepcopy
from json import dumps

import pytest
import yaml

from snowddl.config import SnowDDLConfig
from snowddl.parser import DirectoryScanner, default_parse_sequence

SQL_TOOL = {
    "name": "sql_exec_tool",
    "type": "SYSTEM_EXECUTE_SQL",
    "title": "PULSE_TELEMETRY SQL Execution",
    "description": "Executes SQL using the caller's permissions.",
}


def write_servers(root, schema="OPS", servers=None):
    path = root / "PULSE_TELEMETRY" / schema / "mcp_server.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(servers if servers is not None else {"PULSE_TELEMETRY_MCP": {"tools": [SQL_TOOL]}}))
    return path


def parse_config(root, env_prefix="DEV__", placeholders=None):
    config = SnowDDLConfig(env_prefix)
    for name, value in (placeholders or {}).items():
        config.add_placeholder(name, value)
    scanner = DirectoryScanner(root)
    errors = {}
    for parser_cls in default_parse_sequence:
        parser = parser_cls(config, scanner)
        parser.load_blueprints()
        errors.update(parser.errors)
    return config, scanner, errors


def test_step1_schema_collections_infer_names_and_allow_equal_server_names(tmp_path):
    from snowddl.blueprint import McpServerBlueprint

    write_servers(tmp_path)
    write_servers(tmp_path, "ANALYTICS")
    config, scanner, errors = parse_config(tmp_path)

    assert not errors
    servers = config.get_blueprints_by_type(McpServerBlueprint)
    assert set(servers) == {
        "DEV__PULSE_TELEMETRY.OPS.PULSE_TELEMETRY_MCP",
        "DEV__PULSE_TELEMETRY.ANALYTICS.PULSE_TELEMETRY_MCP",
    }
    assert servers["DEV__PULSE_TELEMETRY.OPS.PULSE_TELEMETRY_MCP"].tools[0].description == SQL_TOOL["description"]
    assert not scanner.get_unused_file_paths()


def test_step1_placeholders_are_resolved_inside_tool_mappings(tmp_path):
    from snowddl.blueprint import McpServerBlueprint

    tool = {**SQL_TOOL, "title": "${{tool_title}}"}
    write_servers(tmp_path, servers={"PULSE_TELEMETRY_MCP": {"tools": [tool]}})
    config, _, errors = parse_config(tmp_path, placeholders={"TOOL_TITLE": "Resolved SQL tool"})

    assert not errors
    server = next(iter(config.get_blueprints_by_type(McpServerBlueprint).values()))
    assert server.tools[0].title == "Resolved SQL tool"


def test_step1_generic_tool_resolves_object_and_warehouse_without_changing_input_schema(tmp_path):
    from snowddl.blueprint import McpServerBlueprint

    tool = {
        **SQL_TOOL,
        "type": "GENERIC",
        "identifier": "TOOLS.MULTIPLY",
        "config": {
            "type": "function",
            "warehouse": "${{warehouse}}",
            "input_schema": {
                "type": "object",
                "properties": {"lowercase_key": {"type": "number", "description": "${{input_description}}"}},
                "required": ["lowercase_key"],
                "additionalProperties": False,
            },
        },
    }
    write_servers(tmp_path, servers={"PULSE_TELEMETRY_MCP": {"tools": [tool]}})
    config, _, errors = parse_config(tmp_path, placeholders={"WAREHOUSE": "COMPUTE", "INPUT_DESCRIPTION": "Input number"})

    assert not errors
    server = next(iter(config.get_blueprints_by_type(McpServerBlueprint).values()))
    assert str(server.tools[0].identifier) == "DEV__PULSE_TELEMETRY.TOOLS.MULTIPLY"
    assert str(server.tools[0].config["warehouse"]) == "DEV__COMPUTE"
    assert server.tools[0].config["input_schema"] == {
        "type": "object",
        "properties": {"lowercase_key": {"type": "number", "description": "Input number"}},
        "required": ["lowercase_key"],
        "additionalProperties": False,
    }


def test_step1_unknown_tool_type_is_rejected_for_programmatic_blueprints(tmp_path):
    from snowddl.blueprint import McpServerBlueprint
    from snowddl.validator import default_validate_sequence

    write_servers(tmp_path)
    config, _, parse_errors = parse_config(tmp_path)
    assert not parse_errors
    server = next(iter(config.get_blueprints_by_type(McpServerBlueprint).values()))
    server.tools[0].type = "TYPO"
    errors = {}
    for validator_cls in default_validate_sequence:
        validator = validator_cls(config)
        validator.validate()
        errors.update(validator.errors)

    assert str(server.full_name) in errors
    assert "tool type" in str(errors[str(server.full_name)])


@pytest.mark.parametrize(
    "tool_type, extra",
    [
        ("SYSTEM_EXECUTE_SQL", {}),
        ("CORTEX_SEARCH_SERVICE_QUERY", {"identifier": "SEARCH_SERVICE"}),
        ("CORTEX_ANALYST_MESSAGE", {"identifier": "SEMANTIC_VIEW"}),
        ("CORTEX_AGENT_RUN", {"identifier": "AGENT", "annotations": {"openWorldHint": False}}),
        (
            "GENERIC",
            {
                "identifier": "FUNCTION",
                "config": {"type": "function", "warehouse": "COMPUTE", "input_schema": {"type": "object"}},
                "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True},
            },
        ),
        ("CODING_AGENT", {"config": {"instructions": {"response": "Summarize results."}}}),
    ],
)
def test_step1_documented_tool_types_are_supported(tmp_path, tool_type, extra):
    from snowddl.blueprint import McpServerBlueprint
    from snowddl.validator import McpServerValidator

    write_servers(tmp_path, servers={"PULSE_TELEMETRY_MCP": {"tools": [{**SQL_TOOL, "type": tool_type, **extra}]}})
    config, _, errors = parse_config(tmp_path)
    assert not errors
    validator = McpServerValidator(config)
    validator.validate()
    assert not validator.errors
    tool = next(iter(config.get_blueprints_by_type(McpServerBlueprint).values())).tools[0]
    if "annotations" in extra:
        assert tool.annotations == extra["annotations"]


@pytest.mark.parametrize(
    "tools, message",
    [
        ([], "1 and 50"),
        ([{**SQL_TOOL, "name": str(index)} for index in range(51)], "1 and 50"),
        ([SQL_TOOL, SQL_TOOL], "Duplicate"),
        ([{**SQL_TOOL, "name": " "}], "empty"),
        ([{**SQL_TOOL, "type": "CORTEX_SEARCH_SERVICE_QUERY"}], "identifier"),
        ([{**SQL_TOOL, "identifier": "UNEXPECTED"}], "identifier"),
        ([{**SQL_TOOL, "config": {}}], "config"),
        ([{**SQL_TOOL, "annotations": {"readOnlyHint": True}}], "annotations"),
        ([{**SQL_TOOL, "type": "GENERIC", "identifier": "FUNCTION"}], "config"),
        (
            [{**SQL_TOOL, "type": "GENERIC", "identifier": "FUNCTION", "config": {"type": "function"}}],
            "config",
        ),
        (
            [
                {
                    **SQL_TOOL,
                    "type": "GENERIC",
                    "identifier": "FUNCTION",
                    "config": {"type": "table", "warehouse": "COMPUTE", "input_schema": {"type": "object"}},
                }
            ],
            "config.type",
        ),
        (
            [
                {
                    **SQL_TOOL,
                    "type": "GENERIC",
                    "identifier": "FUNCTION",
                    "config": {"type": "function", "warehouse": "COMPUTE", "input_schema": {"type": "TYPO"}},
                }
            ],
            "TYPO",
        ),
        ([{**SQL_TOOL, "type": "CODING_AGENT", "identifier": "UNEXPECTED"}], "identifier"),
        ([{**SQL_TOOL, "type": "CODING_AGENT", "config": {"messages": []}}], "messages"),
    ],
)
def test_step1_invalid_tool_specifications_fail_before_execution(tmp_path, tools, message):
    from snowddl.validator import McpServerValidator

    write_servers(tmp_path, servers={"PULSE_TELEMETRY_MCP": {"tools": tools}})
    config, _, errors = parse_config(tmp_path)
    assert not errors
    validator = McpServerValidator(config)
    validator.validate()
    assert validator.errors
    assert message in str(next(iter(validator.errors.values())))


@pytest.mark.parametrize("name", ["OPS.QUALIFIED", "FUNCTION(NUMBER)"])
def test_step1_server_keys_must_be_unqualified_names(tmp_path, name):
    write_servers(tmp_path, servers={name: {"tools": [SQL_TOOL]}})
    _, _, errors = parse_config(tmp_path)
    assert errors


def test_step1_case_collisions_do_not_silently_replace_a_server(tmp_path):
    write_servers(tmp_path, servers={"mcp": {"tools": [SQL_TOOL]}, "MCP": {"tools": [SQL_TOOL]}})
    _, _, errors = parse_config(tmp_path)
    assert errors
    assert "Duplicate" in str(next(iter(errors.values())))


class OfflineCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rows = []

    def execute(self, sql, file_stream=None):
        self.rows = self.connection.execute(sql)
        return self

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def __iter__(self):
        return iter(self.rows)


class OfflineConnection:
    def __init__(self, servers=None, role_grants=None, schemas=("OPS",)):
        self.queries = []
        self.servers = deepcopy(servers or {})
        self.role_grants = deepcopy(role_grants or {})
        self.schemas = schemas

    def cursor(self, *args):
        return OfflineCursor(self)

    def execute(self, sql):
        self.queries.append(sql)
        if "SELECT CURRENT_ACCOUNT()" in sql:
            return [
                {
                    "CURRENT_ACCOUNT": "OFFLINE",
                    "CURRENT_REGION": "OFFLINE",
                    "CURRENT_SESSION": 0,
                    "CURRENT_USER": "OFFLINE_USER",
                    "CURRENT_ROLE": "OFFLINE_ADMIN",
                    "CURRENT_WAREHOUSE": "COMPUTE",
                    "IS_ACCOUNT_ADMIN": False,
                    "IS_SYS_ADMIN": True,
                    "IS_SECURITY_ADMIN": False,
                    "BOOTSTRAP_ACCOUNT": dumps({"serverVersion": "offline", "accountInfo": {"serviceLevelName": "STANDARD"}}),
                    "ACTIVE_BUNDLES": "[]",
                }
            ]
        if sql.startswith("SHOW DATABASES"):
            return [
                {
                    "name": "PULSE_TELEMETRY",
                    "owner": "OFFLINE_ADMIN",
                    "kind": "STANDARD",
                    "options": "",
                    "retention_time": "1",
                    "comment": "",
                }
            ]
        if sql.startswith("SHOW SCHEMAS"):
            return [
                {
                    "database_name": "PULSE_TELEMETRY",
                    "name": schema,
                    "owner": "OFFLINE_ADMIN",
                    "options": "",
                    "retention_time": "1",
                    "comment": "",
                }
                for schema in self.schemas
            ]
        if sql.startswith("SHOW MCP SERVERS"):
            schema = sql.split()[-1].replace('"', "")
            return [
                {
                    "database_name": name.split(".")[0],
                    "schema_name": name.split(".")[1],
                    "name": name.split(".")[2],
                    "owner": "OFFLINE_ADMIN",
                }
                for name in self.servers
                if name.startswith(schema + ".")
            ]
        if sql.startswith("DESCRIBE MCP SERVER"):
            name = sql.split()[-1].replace('"', "")
            return [{"server_spec": dumps(self.servers[name])}]
        if sql.startswith("SHOW PARAMETERS"):
            return []
        if sql.startswith("SHOW ROLES"):
            return [{"name": name, "owner": "OFFLINE_ADMIN", "comment": ""} for name in self.role_grants]
        if sql.startswith("SHOW GRANTS TO ROLE"):
            return deepcopy(self.role_grants[sql.split()[-1].replace('"', "")])
        if sql.startswith("SHOW FUTURE GRANTS"):
            return []
        if sql.startswith(("CREATE MCP SERVER", "CREATE OR REPLACE MCP SERVER")):
            declaration, payload = sql.split(" FROM SPECIFICATION ", 1)
            name = declaration.split()[-1].replace('"', "")
            self.servers[name] = {"version": 1, **decode_specification(payload)}
            for grants in self.role_grants.values():
                grants[:] = [grant for grant in grants if grant["name"] != name]
            return []
        if sql.startswith("GRANT USAGE ON MCP SERVER"):
            declaration, role = sql.split(" TO ROLE ")
            name = declaration.split()[-1].replace('"', "")
            self.role_grants[role.replace('"', "")].append({"privilege": "USAGE", "granted_on": "MCP_SERVER", "name": name})
            return []
        raise AssertionError(f"Unexpected offline SQL: {sql}")


def decode_specification(payload):
    assert payload.startswith("'") and payload.endswith("'")
    return yaml.safe_load(payload[1:-1].replace("''", "'").replace("\\\\", "\\"))


def test_step1_plan_suggests_server_creation_without_executing_ddl(tmp_path):
    from snowddl.engine import SnowDDLEngine
    from snowddl.resolver import McpServerResolver
    from snowddl.settings import SnowDDLSettings

    write_servers(tmp_path)
    config, _, errors = parse_config(tmp_path, env_prefix="")
    assert not errors
    connection = OfflineConnection()
    with SnowDDLEngine(connection, config, SnowDDLSettings(max_workers=1)) as engine:
        resolver = McpServerResolver(engine)
        resolver.resolve()
        engine.flush_thread_buffers()
        assert not resolver.errors
        assert not engine.executed_ddl
        assert len(engine.suggested_ddl) == 1
        assert engine.suggested_ddl[0].startswith('CREATE MCP SERVER "PULSE_TELEMETRY"."OPS"."PULSE_TELEMETRY_MCP"')
    assert not any(query.startswith("CREATE") for query in connection.queries)


def test_step1_specification_change_requires_unsafe_apply(tmp_path):
    from snowddl.engine import SnowDDLEngine
    from snowddl.resolver import McpServerResolver, ResolveResult
    from snowddl.settings import SnowDDLSettings

    write_servers(tmp_path)
    config, _, errors = parse_config(tmp_path, env_prefix="")
    assert not errors
    name = "PULSE_TELEMETRY.OPS.PULSE_TELEMETRY_MCP"
    connection = OfflineConnection({name: {"version": 1, "tools": [{**SQL_TOOL, "description": "Old description"}]}})
    with SnowDDLEngine(connection, config, SnowDDLSettings(max_workers=1, execute_safe_ddl=True)) as engine:
        resolver = McpServerResolver(engine)
        resolver.resolve()
        engine.flush_thread_buffers()
        assert not resolver.errors
        assert resolver.resolved_objects[name] == ResolveResult.REPLACE
        assert not engine.executed_ddl
        assert len(engine.suggested_ddl) == 1
        assert engine.suggested_ddl[0].startswith('CREATE OR REPLACE MCP SERVER "PULSE_TELEMETRY"."OPS".')
    assert connection.servers[name]["tools"][0]["description"] == "Old description"


def test_step1_equivalent_specification_ignores_tool_order_and_native_defaults(tmp_path):
    from snowddl.engine import SnowDDLEngine
    from snowddl.resolver import McpServerResolver, ResolveResult
    from snowddl.settings import SnowDDLSettings

    generic = {
        **SQL_TOOL,
        "name": "multiply",
        "type": "GENERIC",
        "identifier": "MULTIPLY",
        "config": {"type": "function", "warehouse": "COMPUTE", "input_schema": {"type": "object"}},
    }
    coding = {**SQL_TOOL, "name": "coding", "type": "CODING_AGENT"}
    write_servers(tmp_path, servers={"PULSE_TELEMETRY_MCP": {"tools": [SQL_TOOL, generic, coding]}})
    config, _, errors = parse_config(tmp_path, env_prefix="")
    assert not errors
    actual_generic = {
        **generic,
        "identifier": "PULSE_TELEMETRY.OPS.MULTIPLY",
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True},
    }
    name = "PULSE_TELEMETRY.OPS.PULSE_TELEMETRY_MCP"
    connection = OfflineConnection({name: {"version": 1, "tools": [{**coding, "config": {}}, actual_generic, SQL_TOOL]}})
    with SnowDDLEngine(connection, config, SnowDDLSettings(max_workers=1)) as engine:
        resolver = McpServerResolver(engine)
        resolver.resolve()
        engine.flush_thread_buffers()
        assert not resolver.errors
        assert resolver.resolved_objects[name] == ResolveResult.NOCHANGE
        assert not engine.suggested_ddl


def test_step1_replacement_restores_usage_through_existing_technical_role(tmp_path):
    from snowddl.engine import SnowDDLEngine
    from snowddl.resolver import McpServerResolver, ResolveResult, TechnicalRoleResolver
    from snowddl.settings import SnowDDLSettings
    from snowddl.validator import TechnicalRoleValidator

    write_servers(tmp_path)
    name = "PULSE_TELEMETRY.OPS.PULSE_TELEMETRY_MCP"
    role = "MCP_ACCESS__T_ROLE"
    (tmp_path / "technical_role.yaml").write_text(yaml.safe_dump({"MCP_ACCESS": {"grants": {"MCP_SERVER:USAGE": [name]}}}))
    config, _, errors = parse_config(tmp_path, env_prefix="")
    assert not errors
    validator = TechnicalRoleValidator(config)
    validator.validate()
    assert not validator.errors
    connection = OfflineConnection(
        {name: {"version": 1, "tools": [{**SQL_TOOL, "description": "Old description"}]}},
        {role: [{"privilege": "USAGE", "granted_on": "MCP_SERVER", "name": name}]},
    )
    settings = SnowDDLSettings(max_workers=1, execute_safe_ddl=True, execute_unsafe_ddl=True)
    with SnowDDLEngine(connection, config, settings) as engine:
        server_resolver = McpServerResolver(engine)
        server_resolver.resolve()
        assert not server_resolver.errors
        assert not connection.role_grants[role]
        role_resolver = TechnicalRoleResolver(engine)
        role_resolver.resolve()
        assert not role_resolver.errors
        assert connection.role_grants[role] == [{"privilege": "USAGE", "granted_on": "MCP_SERVER", "name": name}]

        server_resolver = McpServerResolver(engine)
        server_resolver.resolve()
        assert server_resolver.resolved_objects[name] == ResolveResult.NOCHANGE
        engine.flush_thread_buffers()
        assert len(engine.executed_ddl) == 2
        assert not engine.suggested_ddl


def test_step1_payload_preserves_quotes_backslashes_dollars_and_unicode(tmp_path):
    from snowddl.engine import SnowDDLEngine
    from snowddl.resolver import McpServerResolver
    from snowddl.settings import SnowDDLSettings

    tool = {**SQL_TOOL, "description": "Apostrophe's $$; DROP TABLE x; -- \\path\nUnicode: café"}
    write_servers(tmp_path, servers={"PULSE_TELEMETRY_MCP": {"tools": [tool]}})
    config, _, errors = parse_config(tmp_path, env_prefix="")
    assert not errors
    connection = OfflineConnection()
    with SnowDDLEngine(connection, config, SnowDDLSettings(max_workers=1, execute_safe_ddl=True)) as engine:
        resolver = McpServerResolver(engine)
        resolver.resolve()
        assert not resolver.errors
    assert connection.servers["PULSE_TELEMETRY.OPS.PULSE_TELEMETRY_MCP"]["tools"] == [tool]


def test_step1_single_database_conversion_updates_identifiers_only(tmp_path):
    from snowddl.app.singledb import SingleDbApp
    from snowddl.blueprint import DatabaseIdent, McpServerBlueprint

    tool = {
        **SQL_TOOL,
        "type": "GENERIC",
        "identifier": "TOOLS.MULTIPLY",
        "config": {
            "type": "procedure",
            "warehouse": "COMPUTE",
            "input_schema": {"properties": {"identifier": {"description": "PULSE_TELEMETRY.OPS.OBJECT"}}},
        },
    }
    write_servers(tmp_path, servers={"PULSE_TELEMETRY_MCP": {"tools": [tool]}})
    config, _, errors = parse_config(tmp_path)
    assert not errors
    source = next(iter(config.get_blueprints_by_type(McpServerBlueprint).values()))
    app = SingleDbApp.__new__(SingleDbApp)
    app.target_db = DatabaseIdent("DEV__", "TARGET")
    converted = app.convert_blueprint(source)
    assert str(converted.full_name) == "DEV__TARGET.OPS.PULSE_TELEMETRY_MCP"
    assert str(converted.tools[0].identifier) == "DEV__TARGET.TOOLS.MULTIPLY"
    assert str(converted.tools[0].config["warehouse"]) == "DEV__COMPUTE"
    assert converted.tools[0].config["input_schema"] == tool["config"]["input_schema"]
    assert str(source.full_name) == "DEV__PULSE_TELEMETRY.OPS.PULSE_TELEMETRY_MCP"


@pytest.mark.parametrize("scope", ["empty", "excluded", "sandbox", "prune"])
def test_step1_reconciliation_respects_management_scope(tmp_path, scope):
    from snowddl.blueprint import ObjectType, SchemaBlueprint
    from snowddl.engine import SnowDDLEngine
    from snowddl.resolver import McpServerResolver
    from snowddl.settings import SnowDDLSettings

    write_servers(tmp_path, servers={} if scope == "empty" else None)
    (tmp_path / "PULSE_TELEMETRY" / "UNMANAGED").mkdir()
    config, _, errors = parse_config(tmp_path, env_prefix="")
    assert not errors
    if scope == "sandbox":
        config.get_blueprints_by_type(SchemaBlueprint)["PULSE_TELEMETRY.OPS"].is_sandbox = True
    excluded = [ObjectType.MCP_SERVER] if scope == "excluded" else []
    name = "PULSE_TELEMETRY.OPS.PULSE_TELEMETRY_MCP"
    old = "PULSE_TELEMETRY.OPS.OLD"
    external = "PULSE_TELEMETRY.UNMANAGED.EXTERNAL"
    connection = OfflineConnection(
        {name: {"tools": [SQL_TOOL]}, old: {"tools": [SQL_TOOL]}, external: {"tools": [SQL_TOOL]}},
        schemas=("OPS", "UNMANAGED"),
    )
    with SnowDDLEngine(connection, config, SnowDDLSettings(max_workers=1, exclude_object_types=excluded)) as engine:
        resolver = McpServerResolver(engine)
        resolver.resolve()
        engine.flush_thread_buffers()
        assert not resolver.errors
        assert not engine.executed_ddl
        if scope in ("empty", "excluded", "sandbox"):
            assert not engine.suggested_ddl
        else:
            assert engine.suggested_ddl == ['DROP MCP SERVER "PULSE_TELEMETRY"."OPS"."OLD"']
    assert not any('SHOW MCP SERVERS IN SCHEMA "PULSE_TELEMETRY"."UNMANAGED"' == query for query in connection.queries)


def test_step1_resolver_registration_preserves_dependency_and_grant_order():
    from snowddl.parser import McpServerParser, singledb_parse_sequence
    from snowddl.resolver import (
        DatabaseRoleResolver,
        McpServerResolver,
        SemanticViewResolver,
        TechnicalRoleResolver,
        default_resolve_sequence,
        singledb_resolve_sequence,
    )

    assert McpServerParser in singledb_parse_sequence
    for sequence in (default_resolve_sequence, singledb_resolve_sequence):
        assert sequence.index(SemanticViewResolver) < sequence.index(McpServerResolver) < sequence.index(DatabaseRoleResolver)
    assert default_resolve_sequence.index(McpServerResolver) < default_resolve_sequence.index(TechnicalRoleResolver)


def test_step1_recursive_placeholders_preserve_scalar_and_list_types(tmp_path):
    from snowddl.parser import McpServerParser, ParsedFile

    path = tmp_path / "values.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "number": "${{number}}",
                "text": "number=${{number}}",
                "items": ["${{choices}}", False, 0, None, ["${{enabled}}", {"value": "${{label}}"}]],
            }
        )
    )
    config = SnowDDLConfig()
    for key, value in {"NUMBER": 3, "CHOICES": [1, True], "ENABLED": False, "LABEL": "nested"}.items():
        config.add_placeholder(key, value)
    parser = McpServerParser(config, DirectoryScanner(tmp_path))
    assert ParsedFile(parser, path, {}).params == {
        "number": 3,
        "text": "number=3",
        "items": [[1, True], False, 0, None, [False, {"value": "nested"}]],
    }


def test_step1_programmatic_annotation_mutation_is_validated(tmp_path):
    from snowddl.blueprint import McpServerBlueprint
    from snowddl.validator import McpServerValidator

    tool = {**SQL_TOOL, "type": "CORTEX_AGENT_RUN", "identifier": "AGENT", "annotations": {"readOnlyHint": True}}
    write_servers(tmp_path, servers={"PULSE_TELEMETRY_MCP": {"tools": [tool]}})
    config, _, errors = parse_config(tmp_path)
    assert not errors
    server = next(iter(config.get_blueprints_by_type(McpServerBlueprint).values()))
    server.tools[0].annotations["readOnlyHint"] = "false"
    validator = McpServerValidator(config)
    validator.validate()
    assert validator.errors


def test_step1_programmatic_server_names_cannot_include_arguments(tmp_path):
    from snowddl.blueprint import McpServerBlueprint, SchemaObjectIdentWithArgs
    from snowddl.validator import McpServerValidator

    write_servers(tmp_path)
    config, _, errors = parse_config(tmp_path)
    assert not errors
    server = next(iter(config.get_blueprints_by_type(McpServerBlueprint).values()))
    config.remove_blueprint(server)
    server.full_name = SchemaObjectIdentWithArgs("DEV__", "PULSE_TELEMETRY", "OPS", "PULSE_TELEMETRY_MCP", data_types=[])
    config.add_blueprint(server)
    validator = McpServerValidator(config)
    validator.validate()
    assert validator.errors
    assert "arguments" in str(next(iter(validator.errors.values())))
