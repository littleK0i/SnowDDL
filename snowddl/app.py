from logging import getLogger, NullHandler
from pathlib import Path
from snowflake.connector import SnowflakeConnection
from typing import Optional

from snowddl.config import SnowDDLConfig
from snowddl.converter import default_converter_sequence
from snowddl.engine import SnowDDLEngine
from snowddl.parser import default_parser_sequence, PlaceholderParser
from snowddl.resolver import default_resolver_sequence
from snowddl.settings import SnowDDLSettings
from snowddl.version import __version__


logger = getLogger(__name__)
logger.addHandler(NullHandler())


class SnowDDLApp:
    def __init__(self):
        self.config: Optional[SnowDDLConfig] = None
        self.engine: Optional[SnowDDLEngine] = None

        self.logger = logger

    def init_config(self, env_prefix):
        self.config = SnowDDLConfig(env_prefix)

    def init_engine(self, connection: SnowflakeConnection, settings: SnowDDLSettings):
        self.engine = SnowDDLEngine(connection, self.config, settings)

    def load_placeholders_with_parsers(self, base_path: Path, placeholder_path: Path = None):
        if placeholder_path and not placeholder_path.is_file():
            raise ValueError(f"Invalid placeholders path [{placeholder_path}]")

        parser = PlaceholderParser(self.config, base_path, placeholder_path)
        parser.load_blueprints()

    def load_blueprints_with_parsers(self, base_path: Path):
        if not base_path.is_dir():
            raise ValueError(f"Invalid config directory [{base_path}]")

        for parser_cls in default_parser_sequence:
            parser = parser_cls(self.config, base_path)
            parser.load_blueprints()

    def resolve_objects(self):
        with self.engine as engine:
            for resolver_cls in default_resolver_sequence:
                resolver = resolver_cls(engine)
                resolver.resolve()

    def destroy_objects(self):
        with self.engine as engine:
            for resolver_cls in default_resolver_sequence:
                resolver = resolver_cls(engine)
                resolver.destroy()

            self.engine.context.destroy_role_with_prefix()

    def convert_objects(self, base_path: Path):
        with self.engine as engine:
            for converter_cls in default_converter_sequence:
                converter = converter_cls(engine, base_path)
                converter.convert()

    def output_context(self):
        roles = []

        if self.engine.context.is_account_admin:
            roles.append("ACCOUNTADMIN")

        if self.engine.context.is_sys_admin:
            roles.append("SYSADMIN")

        if self.engine.context.is_security_admin:
            roles.append("SECURITYADMIN")

        self.logger.info(f"Snowflake version = {self.engine.context.version} ({self.engine.context.edition.name}), SnowDDL version = {__version__}")
        self.logger.info(f"Session = {self.engine.context.current_session}, User = {self.engine.context.current_user}")
        self.logger.info(f"Role = {self.engine.context.current_role}, Warehouse = {self.engine.context.current_warehouse}")
        self.logger.info(f"Roles in session = {','.join(roles)}")
        self.logger.info("---")

    def output_config_errors(self):
        for e in self.config.errors:
            self.logger.warning(f"[{e['path']}]: {e['format_exc']}")

    def output_engine_stats(self):
        self.logger.info(f"Executed {len(self.engine.executed_ddl)} DDL queries, Suggested {len(self.engine.suggested_ddl)} DDL queries")

    def output_suggested_ddl(self):
        if self.engine.suggested_ddl:
            print("--- Suggested DDL ---\n")

        for sql in self.engine.suggested_ddl:
            print(f"{sql};\n")

    def output_executed_ddl(self):
        if self.engine.executed_ddl:
            print("--- Executed DDL ---\n")

        for sql in self.engine.executed_ddl:
            print(f"{sql};\n")
