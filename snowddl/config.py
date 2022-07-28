from collections import defaultdict
from dataclasses import fields
from fnmatch import translate
from pathlib import Path
from re import compile
from typing import List, Dict, Type, Union

from snowddl.blueprint import AbstractBlueprint, AbstractIdentWithPrefix, T_Blueprint


class SnowDDLConfig:
    BUSINESS_ROLE_SUFFIX = 'B_ROLE'
    INBOUND_SHARE_ROLE_SUFFIX = 'IS_ROLE'
    SCHEMA_ROLE_SUFFIX = 'S_ROLE'
    TECH_ROLE_SUFFIX = 'T_ROLE'
    USER_ROLE_SUFFIX = 'U_ROLE'
    WAREHOUSE_ROLE_SUFFIX = 'W_ROLE'

    def __init__(self, env_prefix=None):
        self.env_prefix = self._init_env_prefix(env_prefix)

        self.blueprints: Dict[Type[T_Blueprint], Dict[str,T_Blueprint]] = defaultdict(dict)
        self.errors: List[dict] = []

        self.placeholders: Dict[str,Union[bool,float,int,str]] = {}

    def get_blueprints_by_type(self, cls: Type[T_Blueprint]) -> Dict[str,T_Blueprint]:
        return self.blueprints.get(cls, {})

    def get_blueprints_by_type_and_pattern(self, cls: Type[T_Blueprint], pattern: str) -> Dict[str,T_Blueprint]:
        pattern = pattern.upper()
        type_blueprints = self.blueprints.get(cls, {})

        # Add env prefix to pattern IF blueprint supports it
        for f in fields(cls):
            if f.name == 'full_name':
                if issubclass(f.type, AbstractIdentWithPrefix):
                    pattern = f"{self.env_prefix}{pattern}"

            break

        # Use Unix-style wildcards if any special characters detected in pattern
        if any(special_char in pattern for special_char in ['*', '?', '[', ']']):
            regexp = compile(translate(pattern))

            return {full_name: bp for full_name, bp in type_blueprints.items() if regexp.match(full_name)}

        # Use basic key matching otherwise
        if pattern in type_blueprints:
            return {pattern: type_blueprints[pattern]}

        return {}

    def get_placeholder(self, name: str) -> Union[bool,float,int,str]:
        if name not in self.placeholders:
            raise ValueError(f"Unknown placeholder [{name}]")

        return self.placeholders[name]

    def add_blueprint(self, bp: AbstractBlueprint):
        self.blueprints[bp.__class__][str(bp.full_name)] = bp

    def add_error(self, path: Path, e: Exception):
        self.errors.append({
            "path": path,
            "error": e,
        })

    def add_placeholder(self, name: str, value: Union[bool,float,int,str]):
        self.placeholders[name] = value

    def _init_env_prefix(self, env_prefix):
        if env_prefix:
            env_prefix = str(env_prefix).upper()

            if '__' in env_prefix:
                raise ValueError(f"Env prefix [{env_prefix}] cannot contain [__] double underscore")

            if env_prefix.endswith('_'):
                raise ValueError(f"Env prefix [{env_prefix}] cannot end with [_] underscore")

            return f"{env_prefix}__"

        return ''
