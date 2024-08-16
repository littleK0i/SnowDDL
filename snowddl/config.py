from collections import defaultdict
from fnmatch import translate
from pathlib import Path
from re import compile
from typing import Dict, List, Type, Optional, Union

from snowddl.blueprint import (
    AbstractBlueprint,
    AbstractIdentWithPrefix,
    ObjectType,
    PermissionModel,
    PermissionModelRuleset,
    PermissionModelCreateGrant,
    PermissionModelFutureGrant,
    T_Blueprint,
)


class SnowDDLConfig:
    BUSINESS_ROLE_SUFFIX = "B_ROLE"
    DATABASE_ROLE_SUFFIX = "D_ROLE"
    SCHEMA_ROLE_SUFFIX = "S_ROLE"
    SHARE_ROLE_SUFFIX = "SH_ROLE"
    TECHNICAL_ROLE_SUFFIX = "T_ROLE"
    USER_ROLE_SUFFIX = "U_ROLE"
    WAREHOUSE_ROLE_SUFFIX = "W_ROLE"

    OWNER_ROLE_TYPE = "OWNER"
    WRITE_ROLE_TYPE = "WRITE"
    READ_ROLE_TYPE = "READ"
    USAGE_ROLE_TYPE = "USAGE"
    MONITOR_ROLE_TYPE = "MONITOR"

    DEFAULT_PERMISSION_MODEL = "DEFAULT"

    def __init__(self, env_prefix=None):
        self.env_prefix = self._init_env_prefix(env_prefix)

        self.blueprints: Dict[Type[T_Blueprint], Dict[str, T_Blueprint]] = defaultdict(dict)
        self.errors: List[dict] = []

        self.placeholders: Dict[str, Union[bool, float, int, str]] = {}
        self.permission_models: Dict[str, PermissionModel] = self._init_permission_models()

    def get_blueprints_by_type(self, cls: Type[T_Blueprint]) -> Dict[str, T_Blueprint]:
        return self.blueprints.get(cls, {})

    def get_blueprints_by_type_and_pattern(self, cls: Type[T_Blueprint], pattern: str) -> Dict[str, T_Blueprint]:
        pattern = pattern.upper()
        all_blueprints = self.blueprints.get(cls, {})

        # Simple search by blueprint name for patterns without any special chars
        if not any(special_char in pattern for special_char in ["|", "!", "*", "?", "[", "]"]):
            # Add env prefix to pattern IF blueprint type supports it
            if "full_name" in cls.model_fields and issubclass(cls.model_fields["full_name"].annotation, AbstractIdentWithPrefix):
                pattern = f"{self.env_prefix}{pattern}"

            return {pattern: all_blueprints[pattern]} if pattern in all_blueprints else {}

        include_full_names = set()
        exclude_full_names = set()

        for sub_pattern in pattern.split("|"):
            is_exclude = False

            # Exclude sub-pattern
            if sub_pattern.startswith("!"):
                is_exclude = True
                sub_pattern = sub_pattern[1:]

            # Add env prefix to sub-pattern IF blueprint type supports it
            if "full_name" in cls.model_fields and issubclass(cls.model_fields["full_name"].annotation, AbstractIdentWithPrefix):
                sub_pattern = f"{self.env_prefix}{sub_pattern}"

            regexp = compile(translate(sub_pattern))

            if is_exclude:
                exclude_full_names.update(full_name for full_name in all_blueprints if regexp.match(full_name))
            else:
                include_full_names.update(full_name for full_name in all_blueprints if regexp.match(full_name))

        return {
            full_name: bp
            for full_name, bp in all_blueprints.items()
            if full_name in include_full_names and full_name not in exclude_full_names
        }

    def get_placeholder(self, name: str) -> Union[bool, float, int, str]:
        if name not in self.placeholders:
            raise ValueError(f"Unknown placeholder [{name}]")

        return self.placeholders[name]

    def get_permission_model(self, name: Optional[str]) -> PermissionModel:
        if name is None:
            name = self.DEFAULT_PERMISSION_MODEL
        elif name not in self.permission_models:
            raise ValueError(f"Unknown permission model [{name}]")

        return self.permission_models[name]

    def add_blueprint(self, bp: AbstractBlueprint):
        self.blueprints[bp.__class__][str(bp.full_name)] = bp

    def remove_blueprint(self, bp: AbstractBlueprint):
        if str(bp.full_name) not in self.blueprints.get(bp.__class__, {}):
            raise ValueError(f"Blueprint with type [{bp.__class__.__name__}] and name [{bp.full_name}] does not exist in config")

        del self.blueprints[bp.__class__][str(bp.full_name)]

    def add_error(self, path: Path, e: Exception):
        self.errors.append(
            {
                "path": path,
                "error": e,
            }
        )

    def add_placeholder(self, name: str, value: Union[bool, float, int, str]):
        self.placeholders[name] = value

    def add_permission_model(self, name: str, permission_model: PermissionModel):
        self.permission_models[name] = permission_model

    def _init_env_prefix(self, env_prefix):
        if env_prefix:
            env_prefix = str(env_prefix).upper()

            if "__" in env_prefix:
                raise ValueError(f"Env prefix [{env_prefix}] cannot contain [__] double underscore")

            if env_prefix.endswith("_"):
                raise ValueError(f"Env prefix [{env_prefix}] cannot end with [_] underscore")

            return f"{env_prefix}__"

        return ""

    def _init_permission_models(self):
        return {
            self.DEFAULT_PERMISSION_MODEL: PermissionModel(
                ruleset=PermissionModelRuleset.SCHEMA_OWNER,
                owner_create_grants=[
                    PermissionModelCreateGrant(on=ObjectType.FILE_FORMAT),
                    PermissionModelCreateGrant(on=ObjectType.FUNCTION),
                    PermissionModelCreateGrant(on=ObjectType.PROCEDURE),
                    PermissionModelCreateGrant(on=ObjectType.TABLE),
                    PermissionModelCreateGrant(on=ObjectType.VIEW),
                ],
                owner_future_grants=[
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.ALERT),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.DYNAMIC_TABLE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.EVENT_TABLE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.EXTERNAL_TABLE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.FILE_FORMAT),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.FUNCTION),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.MATERIALIZED_VIEW),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.PIPE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.PROCEDURE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.SEQUENCE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.STAGE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.STREAM),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.TABLE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.TASK),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.VIEW),
                ],
                write_future_grants=[
                    PermissionModelFutureGrant(privilege="READ", on=ObjectType.STAGE),
                    PermissionModelFutureGrant(privilege="WRITE", on=ObjectType.STAGE),
                    PermissionModelFutureGrant(privilege="USAGE", on=ObjectType.STAGE),
                    PermissionModelFutureGrant(privilege="USAGE", on=ObjectType.SEQUENCE),
                    PermissionModelFutureGrant(privilege="INSERT", on=ObjectType.TABLE),
                    PermissionModelFutureGrant(privilege="UPDATE", on=ObjectType.TABLE),
                    PermissionModelFutureGrant(privilege="DELETE", on=ObjectType.TABLE),
                    PermissionModelFutureGrant(privilege="TRUNCATE", on=ObjectType.TABLE),
                ],
                read_future_grants=[
                    PermissionModelFutureGrant(privilege="SELECT", on=ObjectType.DYNAMIC_TABLE),
                    PermissionModelFutureGrant(privilege="SELECT", on=ObjectType.EXTERNAL_TABLE),
                    PermissionModelFutureGrant(privilege="REFERENCES", on=ObjectType.EXTERNAL_TABLE),
                    PermissionModelFutureGrant(privilege="USAGE", on=ObjectType.FILE_FORMAT),
                    PermissionModelFutureGrant(privilege="USAGE", on=ObjectType.FUNCTION),
                    PermissionModelFutureGrant(privilege="SELECT", on=ObjectType.MATERIALIZED_VIEW),
                    PermissionModelFutureGrant(privilege="REFERENCES", on=ObjectType.MATERIALIZED_VIEW),
                    PermissionModelFutureGrant(privilege="USAGE", on=ObjectType.PROCEDURE),
                    PermissionModelFutureGrant(privilege="READ", on=ObjectType.STAGE),
                    PermissionModelFutureGrant(privilege="USAGE", on=ObjectType.STAGE),
                    PermissionModelFutureGrant(privilege="SELECT", on=ObjectType.STREAM),
                    PermissionModelFutureGrant(privilege="SELECT", on=ObjectType.TABLE),
                    PermissionModelFutureGrant(privilege="REFERENCES", on=ObjectType.TABLE),
                    PermissionModelFutureGrant(privilege="SELECT", on=ObjectType.VIEW),
                    PermissionModelFutureGrant(privilege="REFERENCES", on=ObjectType.VIEW),
                ],
            )
        }
