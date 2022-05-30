from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Type, Union

from snowddl.blueprint import AbstractBlueprint, T_Blueprint


class SnowDDLConfig:
    BUSINESS_ROLE_SUFFIX = 'B_ROLE'
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
