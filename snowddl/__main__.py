from argparse import ArgumentParser, HelpFormatter
from logging import getLogger, Formatter, StreamHandler
from os import environ, getcwd
from pathlib import Path
from snowflake.connector import connect
from shutil import rmtree

from snowddl import SnowDDLApp, SnowDDLSettings, ObjectType


def default_entry_point():
    formatter = lambda prog: HelpFormatter(prog, max_help_position=32)
    parser = ArgumentParser(prog='snowddl', description='Object management automation tool for Snowflake', formatter_class=formatter)

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

    # Options
    parser.add_argument('--passphrase', help='Passphrase for private key file (default: SNOWFLAKE_PRIVATE_KEY_PASSPHRASE env variable)', default=environ.get('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE'))
    parser.add_argument('--env-prefix', help='Env prefix added to global object names, used to separate environments (e.g. DEV, PROD)', default=None)
    parser.add_argument('--max-workers', help='Maximum number of workers to resolve objects in parallel', default=None, type=int)
    parser.add_argument('--placeholder-path', help='Path to config file with environment-specific placeholders', default=None)

    # Logging
    parser.add_argument('--log-level', help="Log level (possible values: DEBUG, INFO, WARNING; default: INFO)", default="INFO")
    parser.add_argument('--show-sql', help="Show executed DDL queries", default=False, action='store_true')

    # Object types
    parser.add_argument('--exclude-object-types', help="Comma-separated list of object types NOT to resolve", default=None, metavar='')
    parser.add_argument('--include-object-types', help="Comma-separated list of object types TO resolve, all other types are excluded", default=None, metavar='')

    # Apply even more unsafe changes
    parser.add_argument('--apply-unsafe', help="Additionally apply unsafe changes, which may cause loss of data (ALTER, DROP, etc.)", default=False, action='store_true')
    parser.add_argument('--apply-replace-table', help="Additionally apply REPLACE TABLE when ALTER TABLE is not possible", default=False, action='store_true')
    parser.add_argument('--apply-masking-policy', help="Additionally apply changes to MASKING POLICIES", default=False, action='store_true')
    parser.add_argument('--apply-row-access-policy', help="Additionally apply changes to ROW ACCESS POLICIES", default=False, action='store_true')
    parser.add_argument('--apply-account-params', help="Additionally apply changes to ACCOUNT PARAMETERS", default=False, action='store_true')
    parser.add_argument('--apply-network-policy', help="Additionally apply changes to NETWORK POLICIES", default=False, action='store_true')
    parser.add_argument('--apply-resource-monitor', help="Additionally apply changes to RESOURCE MONITORS", default=False, action='store_true')

    # Refresh state of specific objects
    parser.add_argument('--refresh-user-passwords', help="Additionally refresh passwords of users", default=False, action='store_true')
    parser.add_argument('--refresh-future-grants', help="Additionally refresh missing grants for existing objects derived from future grants", default=False, action='store_true')

    # Destroy without env prefix
    parser.add_argument('--destroy-without-prefix', help="Allow {destroy} action without --env-prefix", default=False, action='store_true')

    # Subparsers
    subparsers = parser.add_subparsers(dest="action")
    subparsers.required = True

    subparsers.add_parser('plan', help="Resolve objects, apply nothing, display suggested changes")
    subparsers.add_parser('apply', help="Resolve objects, apply safe changes, display suggested unsafe changes")
    subparsers.add_parser('destroy', help="Drop objects with specified --env-prefix, use it to reset dev and test environments")

    args = parser.parse_args()

    if not args.a or not args.u or (not args.p and not args.k):
        parser.print_help()
        exit(1)

    logger = get_logger(args)
    config_path = get_config_path(args)
    placeholder_path = get_placeholder_path(args)

    app = SnowDDLApp()
    app.init_config(args.env_prefix)
    app.init_engine(get_connection(args), get_engine_settings(args))

    app.output_context()

    app.load_placeholders_with_parsers(config_path, placeholder_path)

    if app.config.errors:
        app.output_config_errors()
        exit(1)

    app.load_blueprints_with_parsers(config_path)

    if app.config.errors:
        app.output_config_errors()
        exit(1)

    if args.action == 'destroy':
        if not args.env_prefix and not args.destroy_without_prefix:
            raise ValueError("Argument --env-prefix is required for [destroy] action")

        app.destroy_objects()
    else:
        app.resolve_objects()

    app.output_engine_stats()

    if args.show_sql:
        app.output_executed_ddl()

    app.output_suggested_ddl()


def convert_entry_point():
    formatter = lambda prog: HelpFormatter(prog, max_help_position=32)
    parser = ArgumentParser(prog='snowddlconv', description='Convert existing objects in Snowflake account to SnowDDL config', formatter_class=formatter)

    # Config
    parser.add_argument('-c', help='Path to output config directory (default: current directory)', metavar='CONFIG_PATH', default=getcwd())

    # Auth
    parser.add_argument('-a', help='Snowflake account identifier (default: SNOWFLAKE_ACCOUNT env variable)', metavar='ACCOUNT', default=environ.get('SNOWFLAKE_ACCOUNT'))
    parser.add_argument('-u', help='Snowflake user name (default: SNOWFLAKE_USER env variable)', metavar='USER', default=environ.get('SNOWFLAKE_USER'))
    parser.add_argument('-p', help='Snowflake user password (default: SNOWFLAKE_PASSWORD env variable)', metavar='PASSWORD', default=environ.get('SNOWFLAKE_PASSWORD'))
    parser.add_argument('-k', help='Path to private key file (default: SNOWFLAKE_PRIVATE_KEY_PATH env variable)', metavar='PRIVATE_KEY', default=environ.get('SNOWFLAKE_PRIVATE_KEY_PATH'))

    # Role & warehouse
    parser.add_argument('-r', help='Snowflake active role (default: SNOWFLAKE_ROLE env variable)', metavar='ROLE', default=environ.get('SNOWFlAKE_ROLE'))
    parser.add_argument('-w', help='Snowflake active warehouse (default: SNOWFLAKE_WAREHOUSE env variable)', metavar='WAREHOUSE', default=environ.get('SNOWFLAKE_WAREHOUSE'))

    # Options
    parser.add_argument('--passphrase', help='Passphrase for private key file (default: SNOWFLAKE_PRIVATE_KEY_PASSPHRASE env variable)', default=environ.get('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE'))
    parser.add_argument('--env-prefix', help='Env prefix added to global object names, used to separate environments (e.g. DEV, PROD)', default=None)
    parser.add_argument('--max-workers', help='Maximum number of workers to resolve objects in parallel', default=None, type=int)
    parser.add_argument('--clean', help='Delete existing config files before conversion', default=False, action='store_true')

    # Logging
    parser.add_argument('--log-level', help="Log level (possible values: DEBUG, INFO, WARNING; default: INFO)", default="INFO")

    # Object types
    parser.add_argument('--exclude-object-types', help="Comma-separated list of object types NOT to convert", default=None, metavar='')
    parser.add_argument('--include-object-types', help="Comma-separated list of object types TO convert, all other types are excluded", default=None, metavar='')

    args = parser.parse_args()

    if not args.a or not args.u or (not args.p and not args.k):
        parser.print_help()
        exit(1)

    logger = get_logger(args)
    config_path = get_convert_config_path(args)

    app = SnowDDLApp()
    app.init_config(args.env_prefix)
    app.init_engine(get_connection(args), get_convert_engine_settings(args))

    app.output_context()
    app.convert_objects(config_path)


def get_config_path(args):
    config_path = Path(args.c)

    if not config_path.exists():
        config_path = Path(__file__).parent / '_config' / args.c

    if not config_path.exists():
        raise ValueError(f"Config path [{args.c}] does not exist")

    if not config_path.is_dir():
        raise ValueError(f"Config path [{args.c}] is not a directory")

    return config_path.resolve()


def get_placeholder_path(args):
    if args.placeholder_path:
        placeholder_path = Path(args.placeholder_path)

        if not placeholder_path.is_file():
            raise ValueError(f"Placeholder path [{args.placeholder_path}] does not exist or not a file")

        return placeholder_path.resolve()

    return None

def get_convert_config_path(args):
    config_path = Path(args.c)

    if config_path.is_dir() and args.clean:
        rmtree(config_path)

    if not config_path.exists():
        config_path.mkdir(mode=0o755, parents=True)

    if not config_path.is_dir():
        raise ValueError(f"Config path [{args.c}] is not a directory")

    return config_path


def get_logger(args):
    logger = getLogger('snowddl')
    logger.setLevel(args.log_level)

    formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')
    formatter.default_msec_format = '%s.%03d'

    handler = StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def get_connection(args):
    options = {
        "account": args.a,
        "user": args.u,
        "role": args.r,
        "warehouse": args.w,
    }

    if args.k:
        from cryptography.hazmat.primitives import serialization

        key_path = Path(args.k)
        key_password = args.passphrase.encode() if args.passphrase else None

        pk = serialization.load_pem_private_key(data=key_path.read_bytes(), password=key_password)

        options['private_key'] =  pk.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    else:
        options['password'] = args.p

    return connect(**options)


def get_engine_settings(args):
    settings = SnowDDLSettings()

    if args.action == 'apply' or args.action == 'destroy':
        settings.execute_safe_ddl = True

        if args.apply_unsafe:
            settings.execute_unsafe_ddl = True

        if args.apply_replace_table:
            settings.execute_replace_table = True

        if args.apply_masking_policy:
            settings.execute_masking_policy = True

        if args.apply_row_access_policy:
            settings.execute_row_access_policy = True

        if args.apply_account_params:
            settings.execute_account_params = True

        if args.apply_network_policy:
            settings.execute_network_policy = True

        if args.apply_resource_monitor:
            settings.execute_resource_monitor = True

    if args.refresh_user_passwords:
        settings.refresh_user_passwords = True

    if args.refresh_future_grants:
        settings.refresh_future_grants = True

    if args.exclude_object_types:
        try:
            settings.exclude_object_types = [ObjectType[t.strip().upper()] for t in str(args.exclude_object_types).split(',')]
        except KeyError as e:
            raise ValueError(f"Invalid object type [{str(e)}]")

    if args.include_object_types:
        try:
            settings.include_object_types = [ObjectType[t.strip().upper()] for t in str(args.include_object_types).split(',')]
        except KeyError as e:
            raise ValueError(f"Invalid object type [{str(e)}]")

    if args.max_workers:
        settings.max_workers = args.max_workers

    return settings


def get_convert_engine_settings(args):
    settings = SnowDDLSettings()

    if args.exclude_object_types:
        try:
            settings.exclude_object_types = [ObjectType[t.strip().upper()] for t in str(args.exclude_object_types).split(',')]
        except KeyError as e:
            raise ValueError(f"Invalid object type [{str(e)}]")

    if args.include_object_types:
        try:
            settings.include_object_types = [ObjectType[t.strip().upper()] for t in str(args.include_object_types).split(',')]
        except KeyError as e:
            raise ValueError(f"Invalid object type [{str(e)}]")

    if args.max_workers:
        settings.max_workers = args.max_workers

    return settings


if __name__ == '__main__':
    default_entry_point()
