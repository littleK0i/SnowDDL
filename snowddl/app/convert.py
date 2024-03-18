from argparse import ArgumentParser, HelpFormatter
from os import environ, getcwd
from pathlib import Path
from shutil import rmtree

from snowddl.app.base import BaseApp
from snowddl.blueprint import DatabaseIdent, ObjectType
from snowddl.config import SnowDDLConfig
from snowddl.converter import default_converter_sequence
from snowddl.settings import SnowDDLSettings


class ConvertApp(BaseApp):
    def init_arguments_parser(self):
        formatter = lambda prog: HelpFormatter(prog, max_help_position=32)
        parser = ArgumentParser(
            prog="snowddlconv",
            description="Convert existing objects in Snowflake account to SnowDDL config",
            formatter_class=formatter,
        )

        # Config
        parser.add_argument(
            "-c", help="Path to output config directory (default: current directory)", metavar="CONFIG_PATH", default=getcwd()
        )

        # Auth
        parser.add_argument(
            "-a",
            help="Snowflake account identifier (default: SNOWFLAKE_ACCOUNT env variable)",
            metavar="ACCOUNT",
            default=environ.get("SNOWFLAKE_ACCOUNT"),
        )
        parser.add_argument(
            "-u",
            help="Snowflake user name (default: SNOWFLAKE_USER env variable)",
            metavar="USER",
            default=environ.get("SNOWFLAKE_USER"),
        )
        parser.add_argument(
            "-p",
            help="Snowflake user password (default: SNOWFLAKE_PASSWORD env variable)",
            metavar="PASSWORD",
            default=environ.get("SNOWFLAKE_PASSWORD"),
        )
        parser.add_argument(
            "-k",
            help="Path to private key file (default: SNOWFLAKE_PRIVATE_KEY_PATH env variable)",
            metavar="PRIVATE_KEY",
            default=environ.get("SNOWFLAKE_PRIVATE_KEY_PATH"),
        )

        # Role & warehouse
        parser.add_argument(
            "-r",
            help="Snowflake active role (default: SNOWFLAKE_ROLE env variable)",
            metavar="ROLE",
            default=environ.get("SNOWFlAKE_ROLE"),
        )
        parser.add_argument(
            "-w",
            help="Snowflake active warehouse (default: SNOWFLAKE_WAREHOUSE env variable)",
            metavar="WAREHOUSE",
            default=environ.get("SNOWFLAKE_WAREHOUSE"),
        )

        # Options
        parser.add_argument(
            "--authenticator",
            help="Authenticator: 'snowflake' or 'externalbrowser' (to use any IdP and a web browser) (default: SNOWFLAKE_AUTHENTICATOR env variable or 'snowflake')",
            default=environ.get("SNOWFLAKE_AUTHENTICATOR", "snowflake"),
        )
        parser.add_argument(
            "--passphrase",
            help="Passphrase for private key file (default: SNOWFLAKE_PRIVATE_KEY_PASSPHRASE env variable)",
            default=environ.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"),
        )
        parser.add_argument(
            "--env-prefix",
            help="Env prefix added to global object names, used to separate environments (e.g. DEV, PROD)",
            default=environ.get("SNOWFLAKE_ENV_PREFIX"),
        )
        parser.add_argument(
            "--max-workers", help="Maximum number of workers to resolve objects in parallel", default=None, type=int
        )
        parser.add_argument("--clean", help="Delete existing config files before conversion", default=False, action="store_true")

        # Logging
        parser.add_argument(
            "--log-level", help="Log level (possible values: DEBUG, INFO, WARNING; default: INFO)", default="INFO"
        )

        # Object types
        parser.add_argument(
            "--exclude-object-types", help="Comma-separated list of object types NOT to convert", default=None, metavar=""
        )
        parser.add_argument(
            "--include-object-types",
            help="Comma-separated list of object types TO convert, all other types are excluded",
            default=None,
            metavar="",
        )

        # Target specific database only
        parser.add_argument("--include-databases", help="Comma-separated list of databases to convert", default=None, metavar="")
        parser.add_argument(
            "--ignore-ownership",
            help="Ignore OWNERSHIP of databases and schemas during conversion process, makes it possible to convert objects owned by another role",
            default=False,
            action="store_true",
        )

        parser.add_argument(
            "--convert-function-body-to-file", help="Dump out FUNCTION body to separate files", default=False, action="store_true"
        )

        parser.add_argument(
            "--convert-view-text-to-file", help="Dump VIEW text to separate files", default=False, action="store_true"
        )

        return parser

    def init_config_path(self):
        config_path = Path(self.args["c"])

        if config_path.is_dir() and self.args.get("clean"):
            rmtree(config_path)

        if not config_path.exists():
            config_path.mkdir(mode=0o755, parents=True)

        if not config_path.is_dir():
            raise ValueError(f"Config path [{self.args['c']}] is not a directory")

        return config_path

    def init_config(self):
        return SnowDDLConfig(self.args.get("env_prefix"))

    def init_settings(self):
        settings = SnowDDLSettings()

        if self.args.get("exclude_object_types"):
            try:
                settings.exclude_object_types = [
                    ObjectType[t.strip().upper()] for t in str(self.args.get("exclude_object_types")).split(",")
                ]
            except KeyError as e:
                raise ValueError(f"Invalid object type [{str(e)}]")

        if self.args.get("include_object_types"):
            try:
                settings.include_object_types = [
                    ObjectType[t.strip().upper()] for t in str(self.args.get("include_object_types")).split(",")
                ]
            except KeyError as e:
                raise ValueError(f"Invalid object type [{str(e)}]")

        if self.args.get("include_databases"):
            settings.include_databases = [
                DatabaseIdent(self.config.env_prefix, d) for d in str(self.args.get("include_databases")).split(",")
            ]

        if self.args.get("ignore_ownership"):
            settings.ignore_ownership = True

        if self.args.get("add_include_files"):
            settings.add_include_files = True

        if self.args.get("max_workers"):
            settings.max_workers = int(self.args.get("max_workers"))

        if self.args.get("convert_function_body_to_file"):
            settings.convert_function_body_to_file = True

        if self.args.get("convert_view_text_to_file"):
            settings.convert_view_text_to_file = True

        return settings

    def execute(self):
        error_count = 0

        with self.engine:
            self.output_engine_context()

            for converter_cls in default_converter_sequence:
                converter = converter_cls(self.engine, self.config_path)
                converter.convert()

                error_count += len(converter.errors)

            if error_count > 0:
                exit(8)


def entry_point():
    app = ConvertApp()
    app.execute()
