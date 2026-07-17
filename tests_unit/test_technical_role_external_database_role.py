from types import SimpleNamespace

import pytest

from snowddl.blueprint import (
    DatabaseRoleBlueprint,
    DatabaseRoleIdent,
    Grant,
    GrantPattern,
    IdentPattern,
    ObjectType,
    TechnicalRoleBlueprint,
    build_external_database_role_ident,
    build_grant_name_ident,
    build_role_ident,
)
from snowddl.config import SnowDDLConfig
from snowddl.resolver.technical_role import TechnicalRoleResolver
from snowddl.validator.technical_role import TechnicalRoleValidator

ENV_PREFIX = "PYTEST__"


def build_technical_role_blueprint(config, grant_patterns):
    return TechnicalRoleBlueprint(
        full_name=build_role_ident(config.env_prefix, "CORTEX", config.TECHNICAL_ROLE_SUFFIX),
        grant_patterns=grant_patterns,
    )


def build_grant_pattern(privilege="USAGE", on=ObjectType.DATABASE_ROLE, pattern="SNOWFLAKE.CORTEX_USER"):
    return GrantPattern(privilege=privilege, on=on, pattern=IdentPattern(pattern))


class TestIsExternalDatabaseRolePattern:
    def test_accepts_fully_qualified_usage_pattern(self):
        assert build_grant_pattern().is_external_database_role_pattern() is True

    def test_rejects_other_object_type(self):
        assert (
            build_grant_pattern(on=ObjectType.DATABASE, pattern="SNOWFLAKE.CORTEX_USER").is_external_database_role_pattern()
            is False
        )

    def test_rejects_non_usage_privilege(self):
        assert build_grant_pattern(privilege="MONITOR").is_external_database_role_pattern() is False

    def test_rejects_complex_pattern(self):
        assert build_grant_pattern(pattern="SNOWFLAKE.*").is_external_database_role_pattern() is False

    def test_rejects_name_without_database(self):
        assert build_grant_pattern(pattern="CORTEX_USER").is_external_database_role_pattern() is False


class TestTechnicalRoleResolver:
    def build_resolver(self, config):
        return TechnicalRoleResolver(SimpleNamespace(config=config))

    def test_external_database_role_grant(self):
        config = SnowDDLConfig(env_prefix="PYTEST__")
        technical_role_bp = build_technical_role_blueprint(config, [build_grant_pattern()])

        role_bp = self.build_resolver(config).transform_blueprint(technical_role_bp)

        assert role_bp.grants == [
            Grant(
                privilege="USAGE",
                on=ObjectType.DATABASE_ROLE,
                name=DatabaseRoleIdent("", "SNOWFLAKE", "CORTEX_USER"),
            )
        ]
        assert str(role_bp.grants[0].name) == "SNOWFLAKE.CORTEX_USER"

    def test_managed_database_role_takes_precedence(self):
        config = SnowDDLConfig(env_prefix="PYTEST__")
        database_role_bp = DatabaseRoleBlueprint(full_name=DatabaseRoleIdent(config.env_prefix, "ANALYTICS", "READER"))
        config.add_blueprint(database_role_bp)

        technical_role_bp = build_technical_role_blueprint(config, [build_grant_pattern(pattern="ANALYTICS.READER")])

        role_bp = self.build_resolver(config).transform_blueprint(technical_role_bp)

        assert len(role_bp.grants) == 1
        assert role_bp.grants[0].name == database_role_bp.full_name
        assert str(role_bp.grants[0].name).startswith(config.env_prefix)

    def test_unmatched_wildcard_pattern_produces_no_grants(self):
        config = SnowDDLConfig(env_prefix="PYTEST__")
        technical_role_bp = build_technical_role_blueprint(config, [build_grant_pattern(pattern="SNOWFLAKE.*")])

        role_bp = self.build_resolver(config).transform_blueprint(technical_role_bp)

        assert role_bp.grants == []

    def test_round_trip_with_show_grants_ident(self):
        # SHOW GRANTS parsing must produce an ident equal to the config-side ident,
        # otherwise SnowDDL would revoke and re-grant on every apply
        config_side = build_external_database_role_ident("SNOWFLAKE.CORTEX_USER")
        show_grants_side = build_grant_name_ident(ENV_PREFIX, "SNOWFLAKE.CORTEX_USER", ObjectType.DATABASE_ROLE)

        assert config_side == show_grants_side


class TestTechnicalRoleValidator:
    def validate(self, config, grant_patterns):
        bp = build_technical_role_blueprint(config, grant_patterns)
        TechnicalRoleValidator(config).validate_blueprint(bp)

    def test_accepts_external_database_role(self):
        self.validate(SnowDDLConfig(env_prefix="PYTEST__"), [build_grant_pattern()])

    def test_rejects_unmatched_wildcard_pattern(self):
        with pytest.raises(ValueError, match="does not match any objects"):
            self.validate(SnowDDLConfig(env_prefix="PYTEST__"), [build_grant_pattern(pattern="SNOWFLAKE.*")])

    def test_rejects_unmatched_name_without_database(self):
        with pytest.raises(ValueError, match="does not match any objects"):
            self.validate(SnowDDLConfig(env_prefix="PYTEST__"), [build_grant_pattern(pattern="CORTEX_USER")])

    def test_rejects_non_usage_privilege_on_unmatched_pattern(self):
        with pytest.raises(ValueError, match="does not match any objects"):
            self.validate(SnowDDLConfig(env_prefix="PYTEST__"), [build_grant_pattern(privilege="MONITOR")])
