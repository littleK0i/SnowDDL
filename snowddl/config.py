from collections import defaultdict
from pathlib import Path
from traceback import TracebackException
from typing import List, Dict, Type, Union, TYPE_CHECKING

from snowddl.blueprint import AbstractBlueprint, T_Blueprint, BaseDataType, Ident, IdentWithPrefix, ComplexIdentWithPrefix, ComplexIdentWithPrefixAndArgs


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

    def build_complex_ident(self, object_name, context_database_name=None, context_schema_name=None) -> ComplexIdentWithPrefix:
        # Function or procedure identifier with arguments
        if object_name.endswith(')'):
            object_name, data_types_str = object_name.rstrip(')').split('(')
            data_types = [BaseDataType[dt.strip(' ').upper()] for dt in data_types_str.split(',')] if data_types_str else []
        else:
            data_types = None

        parts = object_name.split('.')
        parts_len = len(parts)

        if parts_len > 3:
            raise ValueError(f"Too many delimiters in schema object identifier [{object_name}]")

        # Add context db_name to "schema_name.object_name" or "object_name" identifier
        if parts_len <= 2 and context_database_name:
            parts.insert(0, context_database_name)

        # Add context schema_name to "object_name" identifier
        if parts_len == 1 and context_schema_name:
            parts.insert(1, context_schema_name)

        # Function or procedure identifier with arguments
        if isinstance(data_types, list):
            return ComplexIdentWithPrefixAndArgs(self.env_prefix, *parts, data_types=data_types)
        else:
            return ComplexIdentWithPrefix(self.env_prefix, *parts)

    def build_role_ident(self, *args: Union[Ident, str]) -> IdentWithPrefix:
        parts = [str(a.value) if isinstance(a, Ident) else str(a) for a in args]
        return IdentWithPrefix(self.env_prefix, f"{'__'.join(parts)}")

    def _init_env_prefix(self, env_prefix):
        if env_prefix:
            env_prefix = str(env_prefix).upper()

            if '__' in env_prefix:
                raise ValueError(f"Env prefix [{env_prefix}] cannot contain [__] double underscore")

            if env_prefix.endswith('_'):
                raise ValueError(f"Env prefix [{env_prefix}] cannot end with [_] underscore")

            return f"{env_prefix}__"

        return ''
