from argparse import ArgumentParser, HelpFormatter
from dataclasses import fields, is_dataclass
from os import environ, getcwd
from typing import Optional

from snowddl.app.base import BaseApp
from snowddl.blueprint import AbstractBlueprint, DatabaseBlueprint, DatabaseIdent, SchemaIdent, SchemaObjectIdent, SchemaBlueprint, SchemaObjectBlueprint
from snowddl.config import SnowDDLConfig
from snowddl.parser import singledb_parser_sequence
from snowddl.resolver import singledb_resolver_sequence


class SingleDbApp(BaseApp):
    parser_sequence = singledb_parser_sequence
    resolver_sequence = singledb_resolver_sequence

    def __init__(self):
        self.config_db: Optional[DatabaseIdent] = None
        self.target_db: Optional[DatabaseIdent] = None

        super().__init__()

    def init_arguments_parser(self):
        formatter = lambda prog: HelpFormatter(prog, max_help_position=32)
        parser = ArgumentParser(prog='snowddl-singledb', description='Special SnowDDL mode to process schema objects of single database only', formatter_class=formatter)

        # Config
        parser.add_argument('-c', help='Path to config directory OR name of bundled test config (default: current directory)', metavar='CONFIG_PATH', default=getcwd())

        # Auth
        parser.add_argument('-a', help='Snowflake account identifier (default: SNOWFLAKE_ACCOUNT env variable)', metavar='ACCOUNT', default=environ.get('SNOWFLAKE_ACCOUNT'))
        parser.add_argument('-u', help='Snowflake user name (default: SNOWFLAKE_USER env variable)', metavar='USER', default=environ.get('SNOWFLAKE_USER'))
        parser.add_argument('-p', help='Snowflake user password (default: SNOWFLAKE_PASSWORD env variable)', metavar='PASSWORD', default=environ.get('SNOWFLAKE_PASSWORD'))
        parser.add_argument('-k', help='Path to private key file (default: SNOWFLAKE_PRIVATE_KEY_PATH env variable)', metavar='PRIVATE_KEY', default=environ.get('SNOWFLAKE_PRIVATE_KEY_PATH'))

        # Role & warehouse
        parser.add_argument('-r', help='Snowflake active role (default: SNOWFLAKE_ROLE env variable)', metavar='ROLE', default=environ.get('SNOWFlAKE_ROLE'))
        parser.add_argument('-w', help='Snowflake active warehouse (default: SNOWFLAKE_WAREHOUSE env variable)', metavar='WAREHOUSE', default=environ.get('SNOWFLAKE_WAREHOUSE'))

        # SingleDb options
        parser.add_argument('--config-db', help='Source database name in config (default: detected automatically if only one database is present in config)', default=None)
        parser.add_argument('--target-db', help='Target database name in Snowflake account (default: same as --config-db)', default=None)

        # Generic options
        parser.add_argument('--passphrase', help='Passphrase for private key file (default: SNOWFLAKE_PRIVATE_KEY_PASSPHRASE env variable)', default=environ.get('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE'))
        parser.add_argument('--env-prefix', help='Env prefix added to global object names, used to separate environments (e.g. DEV, PROD)', default=environ.get('SNOWFLAKE_ENV_PREFIX'))
        parser.add_argument('--max-workers', help='Maximum number of workers to resolve objects in parallel', default=None, type=int)

        # Logging
        parser.add_argument('--log-level', help="Log level (possible values: DEBUG, INFO, WARNING; default: INFO)", default="INFO")
        parser.add_argument('--show-sql', help="Show executed DDL queries", default=False, action='store_true')

        # Placeholders
        parser.add_argument('--placeholder-path', help='Path to config file with environment-specific placeholders', default=None, metavar='')
        parser.add_argument('--placeholder-values', help='Environment-specific placeholder values in JSON format', default=None, metavar='')

        # Object types
        parser.add_argument('--exclude-object-types', help="Comma-separated list of object types NOT to resolve", default=None, metavar='')
        parser.add_argument('--include-object-types', help="Comma-separated list of object types TO resolve, all other types are excluded", default=None, metavar='')

        # Apply even more unsafe changes
        parser.add_argument('--apply-unsafe', help="Additionally apply unsafe changes, which may cause loss of data (ALTER, DROP, etc.)", default=False, action='store_true')
        parser.add_argument('--apply-replace-table', help="Additionally apply REPLACE TABLE when ALTER TABLE is not possible", default=False, action='store_true')
        parser.add_argument('--apply-masking-policy', help="Additionally apply changes to MASKING POLICIES", default=False, action='store_true')
        parser.add_argument('--apply-row-access-policy', help="Additionally apply changes to ROW ACCESS POLICIES", default=False, action='store_true')

        # Subparsers
        subparsers = parser.add_subparsers(dest="action")
        subparsers.required = True

        subparsers.add_parser('plan', help="Resolve objects, apply nothing, display suggested changes")
        subparsers.add_parser('apply', help="Resolve objects, apply safe changes, display suggested unsafe changes")
        subparsers.add_parser('destroy', help="Drop objects with specified --env-prefix, use it to reset dev and test environments")

        return parser

    def init_config(self):
        config = super().init_config()

        # Init Source DB
        if self.args.get('config_db'):
            self.config_db = DatabaseIdent(config.env_prefix, self.args.get('config_db'))

            if str(self.config_db) not in config.get_blueprints_by_type(DatabaseBlueprint):
                raise ValueError(f"Source database [{self.config_db}] does not exist in config")
        else:
            if len(config.get_blueprints_by_type(DatabaseBlueprint)) > 1:
                raise ValueError(f"More than one source database exist in config, please choose a specific database using --source-db argument")

            self.config_db = next(iter(config.get_blueprints_by_type(DatabaseBlueprint).values())).full_name

        # Init Target DB
        if self.args.get('target_db'):
            self.target_db = DatabaseIdent(config.env_prefix, self.args.get('target_db'))
        else:
            self.target_db = self.config_db

        return self.convert_config(config)

    def convert_config(self, original_config: SnowDDLConfig):
        singledb_config = SnowDDLConfig(self.args.get('env_prefix'))

        for bp_dict in original_config.blueprints.values():
            for bp in bp_dict.values():
                if isinstance(bp, (SchemaBlueprint, SchemaObjectBlueprint)) and bp.full_name.database_full_name == self.config_db:
                    singledb_config.add_blueprint(self.convert_blueprint(bp))

        return singledb_config

    def convert_blueprint(self, bp: AbstractBlueprint):
        for f in fields(bp):
            self.convert_object_recursive(getattr(bp, f.name))

        return bp

    def convert_object_recursive(self, obj):
        if is_dataclass(obj):
            for f in fields(obj):
                self.convert_object_recursive(getattr(obj, f.name))

        if isinstance(obj, list):
            for item in obj:
                self.convert_object_recursive(item)

        if isinstance(obj, dict):
            for item in obj.values():
                self.convert_object_recursive(item)

        if isinstance(obj, (SchemaIdent, SchemaObjectIdent)):
            obj.database = self.target_db.database

        return obj

    def init_settings(self):
        settings = super().init_settings()
        settings.include_databases = [self.target_db]
        settings.ignore_ownership = True

        return settings


def entry_point():
    app = SingleDbApp()
    app.execute()
