from collections import defaultdict
from fnmatch import translate
from pathlib import Path
from re import compile
from typing import Dict, List, Type, Union

from snowddl.blueprint import AbstractBlueprint, AbstractIdentWithPrefix, PermissionModel, T_Blueprint


class SnowDDLConfig:
    BUSINESS_ROLE_SUFFIX = "B_ROLE"
    DATABASE_ROLE_SUFFIX = "D_ROLE"
    INBOUND_SHARE_ROLE_SUFFIX = "IS_ROLE"
    SCHEMA_ROLE_SUFFIX = "S_ROLE"
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
        self.permission_models: Dict[str, PermissionModel] = {}

    def get_blueprints_by_type(self, cls: Type[T_Blueprint]) -> Dict[str, T_Blueprint]:
        return self.blueprints.get(cls, {})

    def get_blueprints_by_type_and_pattern(self, cls: Type[T_Blueprint], pattern: str) -> Dict[str, T_Blueprint]:
        pattern = pattern.upper()
        type_blueprints = self.blueprints.get(cls, {})

        # Add env prefix to pattern IF blueprint supports it
        if "full_name" in cls.model_fields and issubclass(cls.model_fields["full_name"].annotation, AbstractIdentWithPrefix):
            pattern = f"{self.env_prefix}{pattern}"

        # Use Unix-style wildcards if any special characters detected in pattern
        if any(special_char in pattern for special_char in ["*", "?", "[", "]"]):
            regexp = compile(translate(pattern))

            return {full_name: bp for full_name, bp in type_blueprints.items() if regexp.match(full_name)}

        # Use basic key matching otherwise
        if pattern in type_blueprints:
            return {pattern: type_blueprints[pattern]}

        return {}

    def get_placeholder(self, name: str) -> Union[bool, float, int, str]:
        if name not in self.placeholders:
            raise ValueError(f"Unknown placeholder [{name}]")

        return self.placeholders[name]

    def get_permission_model(self, name: str) -> PermissionModel:
        if name not in self.permission_models:
            raise ValueError(f"Unknown permission model [{name}]")

        return self.permission_models[name]

    def add_blueprint(self, bp: AbstractBlueprint):
        self.blueprints[bp.__class__][str(bp.full_name)] = bp

    def remove_blueprint(self, bp: AbstractBlueprint):
        if str(bp.full_name) not in self.blueprints.get(bp.__class__, {}):
            raise ValueError(f"Blueprint with type [{bp.__class__.__name__}] and name [{bp.full_name}] does not exist in config")

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
