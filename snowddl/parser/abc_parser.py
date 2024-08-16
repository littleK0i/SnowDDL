from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict, List, Union

from snowddl.config import SnowDDLConfig
from snowddl.blueprint import (
    AccountGrant,
    BaseDataType,
    DatabaseRoleIdent,
    Grant,
    Ident,
    NameWithType,
    ObjectType,
    ShareRoleBlueprint,
    build_role_ident,
)
from snowddl.parser._parsed_file import ParsedFile


class AbstractParser(ABC):
    def __init__(self, config: SnowDDLConfig, base_path: Path):
        self.config = config
        self.base_path = base_path

        self.env_prefix = config.env_prefix

    @abstractmethod
    def load_blueprints(self):
        pass

    def parse_single_file(self, path: Path, json_schema: dict, callback: Callable[[ParsedFile], Union[None, Dict]] = None):
        if not callback:
            callback = lambda f: f.params

        if path.exists():
            try:
                file = ParsedFile(self, path, json_schema)
                return callback(file)
            except Exception as e:
                self.config.add_error(path, e)

        return {}

    def parse_schema_object_files(self, object_type: str, json_schema: dict, callback: Callable[[ParsedFile], None]):
        for path in self.base_path.glob(f"*/*/{object_type}/*.yaml"):
            try:
                file = ParsedFile(self, path, json_schema)
                callback(file)
            except Exception as e:
                self.config.add_error(path, e)

    def normalise_params_dict(self, params):
        if params is None:
            return None

        if isinstance(params, dict):
            return {k.upper(): v for k, v in params.items()}

        raise ValueError(f"Value is neither None, nor dictionary [{params}]")

    def normalise_stage_path(self, stage_path):
        if stage_path is None:
            return None

        stage_path = str(stage_path)

        if not stage_path.startswith("/"):
            stage_path = f"/{stage_path}"

        return stage_path

    def validate_name_with_args(self, path: Path, arguments: List[NameWithType]):
        stem_name = str(path.stem)
        args_str = ",".join([a.type.base_type.name for a in arguments]).lower()

        open_pos = stem_name.find("(")
        close_pos = stem_name.find(")")

        if open_pos == -1 or close_pos == -1:
            raise ValueError(f"File [{path}] name should have list of arguments, e.g. [{stem_name}({args_str}).yaml]")

        base_name = stem_name[:open_pos]

        if stem_name[open_pos + 1 : close_pos] != args_str:
            raise ValueError(f"File [{path}] name does not match list of arguments, expected [{base_name}({args_str}).yaml]")

        # Snowflake bug: case 00444370
        # TIME and TIMESTAMP-like arguments with non-default precision are currently bugged in Snowflake
        # This check will be removed when the problem is fixed or workaround is provided
        for a in arguments:
            if (
                a.type.base_type
                in (BaseDataType.TIME, BaseDataType.TIMESTAMP_LTZ, BaseDataType.TIMESTAMP_NTZ, BaseDataType.TIMESTAMP_TZ)
                and a.type.val1 != 9
            ):
                raise ValueError(
                    f"Argument [{a.name}] with data type [{a.type.base_type.name}] must have precision of 9 (default) instead of [{a.type.val1}] due to known bug in Snowflake (case 00444370)"
                )

        return base_name

    def build_share_role_grant(self, share_name):
        return Grant(
            privilege="USAGE",
            on=ObjectType.ROLE,
            name=build_role_ident(self.env_prefix, share_name, self.config.SHARE_ROLE_SUFFIX),
        )

    def build_share_role_blueprint(self, share_name):
        return ShareRoleBlueprint(
            full_name=build_role_ident(self.env_prefix, share_name, self.config.SHARE_ROLE_SUFFIX),
            grants=[
                Grant(
                    privilege="IMPORTED PRIVILEGES",
                    on=ObjectType.DATABASE,
                    name=Ident(share_name),
                ),
            ],
        )

    def build_warehouse_role_grant(self, warehouse_name, grant_type):
        return Grant(
            privilege="USAGE",
            on=ObjectType.ROLE,
            name=build_role_ident(self.env_prefix, warehouse_name, grant_type, self.config.WAREHOUSE_ROLE_SUFFIX),
        )

    def build_technical_role_grant(self, technical_role_name):
        return Grant(
            privilege="USAGE",
            on=ObjectType.ROLE,
            name=build_role_ident(self.env_prefix, technical_role_name, self.config.TECHNICAL_ROLE_SUFFIX),
        )

    def build_account_grant(self, privilege):
        return AccountGrant(privilege=privilege.upper())

    def build_global_role_grant(self, global_role_name):
        if "." in global_role_name:
            return Grant(
                privilege="USAGE",
                on=ObjectType.DATABASE_ROLE,
                name=DatabaseRoleIdent("", *global_role_name.split(".", 2)),
            )

        return Grant(
            privilege="USAGE",
            on=ObjectType.ROLE,
            name=Ident(global_role_name),
        )

    def build_integration_usage_grant(self, integration_name):
        return Grant(
            privilege="USAGE",
            on=ObjectType.INTEGRATION,
            name=Ident(integration_name),
        )
