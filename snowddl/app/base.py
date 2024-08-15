from argparse import ArgumentParser, HelpFormatter
from cryptography.hazmat.primitives import serialization
from importlib.util import module_from_spec, spec_from_file_location
from json import loads as json_loads
from json.decoder import JSONDecodeError
from logging import getLogger, Formatter, StreamHandler
from os import environ, getcwd
from pathlib import Path
from snowflake.connector import connect
from traceback import TracebackException

from snowddl.blueprint import Ident, ObjectType
from snowddl.config import SnowDDLConfig
from snowddl.engine import SnowDDLEngine
from snowddl.parser import default_parser_sequence, PermissionModelParser, PlaceholderParser
from snowddl.resolver import default_resolver_sequence
from snowddl.settings import SnowDDLSettings
from snowddl.version import __version__


class BaseApp:
    application_name = "SnowDDL"
    application_version = __version__

    parser_sequence = default_parser_sequence
    resolver_sequence = default_resolver_sequence

    def __init__(self):
        self.arg_parser = self.init_arguments_parser()
        self.args = self.init_arguments()
        self.logger = self.init_logger()

        self.config_path = self.init_config_path()
        self.config = self.init_config()
        self.settings = self.init_settings()

        self.engine = self.init_engine()

    def init_arguments_parser(self):
        formatter = lambda prog: HelpFormatter(prog, max_help_position=36)

        parser = ArgumentParser(
            prog="snowddl", description="Object management automation tool for Snowflake", formatter_class=formatter
        )

        # Config
        parser.add_argument(
            "-c",
            help="Path to config directory OR name of bundled test config (default: current directory)",
            metavar="CONFIG_PATH",
            default=getcwd(),
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
            "--env-admin-role",
            help="Super administration role which should inherit env prefixed SnowDDL role",
            default=environ.get("SNOWFLAKE_ENV_ADMIN_ROLE"),
        )
        parser.add_argument(
            "--max-workers", help="Maximum number of workers to resolve objects in parallel", default=None, type=int
        )
        parser.add_argument(
            "--query-tag",
            help="Add QUERY_TAG to all queries produced by SnowDDL",
            default=environ.get("SNOWFLAKE_QUERY_TAG"),
        )

        # Logging
        parser.add_argument(
            "--log-level", help="Log level (possible values: DEBUG, INFO, WARNING; default: INFO)", default="INFO"
        )
        parser.add_argument("--show-sql", help="Show executed DDL queries", default=False, action="store_true")

        # Placeholders
        parser.add_argument(
            "--placeholder-path", help="Path to config file with environment-specific placeholders", default=None, metavar=""
        )
        parser.add_argument(
            "--placeholder-values", help="Environment-specific placeholder values in JSON format", default=None, metavar=""
        )

        # Object types
        parser.add_argument(
            "--exclude-object-types", help="Comma-separated list of object types NOT to resolve", default=None, metavar=""
        )
        parser.add_argument(
            "--include-object-types",
            help="Comma-separated list of object types TO resolve, all other types are excluded",
            default=None,
            metavar="",
        )

        # Apply even more unsafe changes
        parser.add_argument(
            "--apply-unsafe",
            help="Additionally apply unsafe changes, which may cause loss of data (ALTER, DROP, etc.)",
            default=False,
            action="store_true",
        )
        parser.add_argument(
            "--apply-replace-table",
            help="Additionally apply REPLACE TABLE when ALTER TABLE is not possible",
            default=False,
            action="store_true",
        )
        parser.add_argument(
            "--apply-all-policy", help="Additionally apply changes to all types of POLICIES", default=False, action="store_true"
        )
        parser.add_argument(
            "--apply-aggregation-policy",
            help="Additionally apply changes to AGGREGATION POLICIES",
            default=False,
            action="store_true",
        )
        parser.add_argument(
            "--apply-masking-policy", help="Additionally apply changes to MASKING POLICIES", default=False, action="store_true"
        )
        parser.add_argument(
            "--apply-projection-policy",
            help="Additionally apply changes to PROJECTION POLICIES",
            default=False,
            action="store_true",
        )
        parser.add_argument(
            "--apply-row-access-policy",
            help="Additionally apply changes to ROW ACCESS POLICIES",
            default=False,
            action="store_true",
        )
        parser.add_argument(
            "--apply-account-params", help="Additionally apply changes to ACCOUNT PARAMETERS", default=False, action="store_true"
        )
        parser.add_argument(
            "--apply-network-policy", help="Additionally apply changes to NETWORK POLICIES", default=False, action="store_true"
        )
        parser.add_argument(
            "--apply-resource-monitor", help="Additionally apply changes to RESOURCE MONITORS", default=False, action="store_true"
        )
        parser.add_argument(
            "--apply-outbound-share", help="Additionally apply changes to OUTBOUND SHARES", default=False, action="store_true"
        )

        # Refresh state of specific objects
        parser.add_argument(
            "--refresh-user-passwords", help="Additionally refresh passwords of users", default=False, action="store_true"
        )
        parser.add_argument(
            "--refresh-future-grants",
            help="Additionally refresh missing grants for existing objects derived from future grants",
            default=False,
            action="store_true",
        )
        parser.add_argument(
            "--refresh-stage-encryption",
            help="Additionally refresh stage encryption parameters for existing external stages",
            default=False,
            action="store_true",
        )
        parser.add_argument(
            "--refresh-secrets",
            help="Additionally refresh secrets",
            default=False,
            action="store_true",
        )

        # Cloning
        parser.add_argument(
            "--clone-table",
            help="Clone all tables from source databases (without env_prefix) to destination databases (with env_prefix)",
            default=False,
            action="store_true",
        )

        # Destroy without env prefix
        parser.add_argument(
            "--destroy-without-prefix", help="Allow {destroy} action without --env-prefix", default=False, action="store_true"
        )

        # Subparsers
        subparsers = parser.add_subparsers(dest="action")
        subparsers.required = True

        subparsers.add_parser("plan", help="Resolve objects, apply nothing, display suggested changes")
        subparsers.add_parser("apply", help="Resolve objects, apply safe changes, display suggested unsafe changes")
        subparsers.add_parser(
            "destroy", help="Drop objects with specified --env-prefix, use it to reset dev and test environments"
        )

        return parser

    def init_arguments(self):
        args = vars(self.arg_parser.parse_args())

        if not self.validate_auth_args(args):
            self.arg_parser.print_help()
            exit(1)

        return args

    def validate_auth_args(self, args):
        if args["authenticator"] == "snowflake":
            if not args["a"] or not args["u"] or (not args["p"] and not args["k"] and "SNOWFLAKE_PRIVATE_KEY" not in environ):
                return False
        elif args["authenticator"] == "externalbrowser":
            if not args["a"] or not args["u"]:
                return False
        elif args["authenticator"] is not None:
            return False
        return True

    def init_logger(self):
        logger = getLogger("snowddl")
        logger.setLevel(self.args.get("log_level", "INFO"))

        formatter = Formatter("%(asctime)s - %(levelname)s - %(message)s")
        formatter.default_msec_format = "%s.%03d"

        handler = StreamHandler()
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        return logger

    def init_config_path(self):
        config_path = Path(self.args["c"])

        if not config_path.exists():
            config_path = Path(__file__).parent.parent / "_config" / self.args["c"]

        if not config_path.exists():
            raise ValueError(f"Config path [{self.args['c']}] does not exist")

        if not config_path.is_dir():
            raise ValueError(f"Config path [{self.args['c']}] is not a directory")

        return config_path.resolve()

    def init_config(self):
        config = SnowDDLConfig(self.args.get("env_prefix"))

        # Placeholders
        placeholder_path = self.get_placeholder_path()
        placeholder_values = self.get_placeholder_values()

        parser = PlaceholderParser(config, self.config_path)
        parser.load_placeholders(placeholder_path, placeholder_values, self.args)

        if config.errors:
            self.output_config_errors(config)
            exit(1)

        # Permission models
        parser = PermissionModelParser(config, self.config_path)
        parser.load_permission_models()

        if config.errors:
            self.output_config_errors(config)
            exit(1)

        # Blueprints
        for parser_cls in self.parser_sequence:
            parser = parser_cls(config, self.config_path)
            parser.load_blueprints()

        if config.errors:
            self.output_config_errors(config)
            exit(1)

        # Custom programmatically generated blueprints and config adjustments
        for module_path in sorted(self.config_path.glob("__custom/*.py")):
            try:
                spec = spec_from_file_location(module_path.name, module_path)

                module = module_from_spec(spec)
                spec.loader.exec_module(module)

                module.handler(config)
            except Exception as e:
                config.add_error(module_path, e)

        if config.errors:
            self.output_config_errors(config)
            exit(1)

        return config

    def init_settings(self):
        settings = SnowDDLSettings()

        if self.args.get("action") in ("apply", "destroy"):
            settings.execute_safe_ddl = True

            if self.args.get("apply_unsafe") or self.args.get("action") == "destroy":
                settings.execute_unsafe_ddl = True

            if self.args.get("apply_replace_table"):
                settings.execute_replace_table = True

            if self.args.get("apply_all_policy"):
                settings.execute_aggregation_policy = True
                settings.execute_masking_policy = True
                settings.execute_projection_policy = True
                settings.execute_row_access_policy = True
                settings.execute_network_policy = True

            if self.args.get("apply_aggregation_policy"):
                settings.execute_aggregation_policy = True

            if self.args.get("apply_masking_policy"):
                settings.execute_masking_policy = True

            if self.args.get("apply_projection_policy"):
                settings.execute_projection_policy = True

            if self.args.get("apply_row_access_policy"):
                settings.execute_row_access_policy = True

            if self.args.get("apply_account_params"):
                settings.execute_account_params = True

            if self.args.get("apply_network_policy"):
                settings.execute_network_policy = True

            if self.args.get("apply_resource_monitor"):
                settings.execute_resource_monitor = True

            if self.args.get("apply_outbound_share"):
                settings.execute_outbound_share = True

        if self.args.get("refresh_user_passwords"):
            settings.refresh_user_passwords = True

        if self.args.get("refresh_future_grants"):
            settings.refresh_future_grants = True

        if self.args.get("refresh_stage_encryption"):
            settings.refresh_stage_encryption = True

        if self.args.get("refresh_secrets"):
            settings.refresh_secrets = True

        if self.args.get("clone_table"):
            if self.args.get("action") != "apply":
                raise ValueError("Argument --clone-table requires action [apply]")

            if not self.args.get("env_prefix"):
                raise ValueError("Argument --clone-table requires argument --env-prefix")

            settings.clone_table = True

        if self.args.get("env_admin_role"):
            settings.env_admin_role = Ident(self.args.get("env_admin_role"))

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

        if self.args.get("max_workers"):
            settings.max_workers = int(self.args.get("max_workers"))

        return settings

    def init_engine(self):
        return SnowDDLEngine(self.get_connection(), self.config, self.settings)

    def get_connection(self):
        options = {
            "account": self.args["a"],
            "user": self.args["u"],
            "role": self.args["r"],
            "warehouse": self.args["w"],
            "application": f"{self.application_name} {self.application_version}",
        }

        if self.args.get("authenticator") == "snowflake":
            key_bytes = None

            if self.args.get("k"):
                key_path = Path(self.args.get("k"))

                if not key_path.is_file():
                    raise ValueError(f"Private key file [{key_path}] does not exist or not a file")

                key_bytes = key_path.read_bytes()
            elif "SNOWFLAKE_PRIVATE_KEY" in environ:
                key_bytes = str(environ["SNOWFLAKE_PRIVATE_KEY"]).encode("utf-8")

            if key_bytes:
                key_password = str(self.args.get("passphrase")).encode("utf-8") if self.args.get("passphrase") else None
                pk = serialization.load_pem_private_key(data=key_bytes, password=key_password)

                options["private_key"] = pk.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            else:
                options["password"] = self.args["p"]
        elif self.args.get("authenticator") == "externalbrowser":
            options["authenticator"] = "externalbrowser"
        else:
            raise ValueError("Only 'snowflake' and 'externalbrowser' authenticators are supported")

        if self.args.get("query_tag"):
            options["session_parameters"] = {
                "QUERY_TAG": self.args.get("query_tag"),
            }

        return connect(**options)

    def execute(self):
        error_count = 0

        with self.engine:
            self.output_engine_context()

            if self.args.get("action") == "destroy":
                if not self.args.get("env_prefix") and not self.args.get("destroy_without_prefix"):
                    raise ValueError("Argument --env-prefix is required for [destroy] action")

                for resolver_cls in self.resolver_sequence:
                    resolver = resolver_cls(self.engine)
                    resolver.destroy()

                    error_count += len(resolver.errors)

                self.engine.context.destroy_role_with_prefix()
            else:
                for resolver_cls in self.resolver_sequence:
                    resolver = resolver_cls(self.engine)
                    resolver.resolve()

                    error_count += len(resolver.errors)

            self.engine.connection.close()
            self.output_engine_stats()
            self.output_engine_warnings()

            if self.args.get("show_sql"):
                self.output_executed_ddl()

            self.output_suggested_ddl()

            if error_count > 0:
                exit(8)

    def output_engine_context(self):
        roles = []

        if self.engine.context.is_account_admin:
            roles.append("ACCOUNTADMIN")

        if self.engine.context.is_sys_admin:
            roles.append("SYSADMIN")

        if self.engine.context.is_security_admin:
            roles.append("SECURITYADMIN")

        self.logger.info(
            f"Snowflake version = {self.engine.context.version} ({self.engine.context.edition.name}), SnowDDL version = {__version__}"
        )
        self.logger.info(f"Account = {self.engine.context.current_account}, Region = {self.engine.context.current_region}")
        self.logger.info(f"Session = {self.engine.context.current_session}, User = {self.engine.context.current_user}")
        self.logger.info(f"Role = {self.engine.context.current_role}, Warehouse = {self.engine.context.current_warehouse}")
        self.logger.info(f"Roles in session = {','.join(roles)}")
        self.logger.info("---")

    def get_placeholder_path(self):
        if self.args.get("placeholder_path"):
            placeholder_path = Path(self.args.get("placeholder_path"))

            if not placeholder_path.is_file():
                raise ValueError(f"Placeholder path [{self.args.get('placeholder_path')}] does not exist or not a file")

            return placeholder_path.resolve()

        return None

    def get_placeholder_values(self):
        if self.args.get("placeholder_values"):
            try:
                placeholder_values = json_loads(self.args.get("placeholder_values"))
            except JSONDecodeError:
                raise ValueError(f"Placeholder values [{self.args.get('placeholder_values')}] are not a valid JSON")

            if not isinstance(placeholder_values, dict):
                raise ValueError(f"Placeholder values [{self.args.get('placeholder_values')}] are not JSON encoded dict")

            for k, v in placeholder_values.items():
                if not isinstance(v, (bool, float, int, str)):
                    raise ValueError(
                        f"Invalid type [{type(v)}] of placeholder [{k.upper()}] value, supported types are: bool, float, int, str"
                    )

            return placeholder_values

        return None

    def output_config_errors(self, config):
        for e in config.errors:
            self.logger.warning(f"[{e['path']}]: {''.join(TracebackException.from_exception(e['error']).format())}")

    def output_engine_stats(self):
        self.logger.info(
            f"Executed {len(self.engine.executed_ddl)} DDL queries, Suggested {len(self.engine.suggested_ddl)} DDL queries"
        )

    def output_engine_warnings(self):
        for object_type, object_names in self.engine.intention_cache.invalid_name_warning.items():
            for name in object_names:
                self.logger.warning(
                    f"Detected {object_type.name} with name [{name}] "
                    f"which does not conform to SnowDDL standards, please rename or drop it manually"
                )

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


def entry_point():
    app = BaseApp()
    app.execute()
