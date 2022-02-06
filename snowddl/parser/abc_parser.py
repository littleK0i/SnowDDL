from abc import ABC, abstractmethod
from dataclasses import dataclass
from json import loads
from jsonschema import validate
from pathlib import Path
from typing import Optional
from yaml import safe_load

from snowddl.config import SnowDDLConfig
from snowddl.blueprint import ComplexIdentWithPrefix, ComplexIdentWithPrefixAndArgs


class AbstractParser(ABC):
    yaml_suffix = '.yaml'

    def __init__(self, config: SnowDDLConfig, base_path: Path):
        self.config = config
        self.base_path = base_path

        self.env_prefix = config.env_prefix

    @abstractmethod
    def load_blueprints(self):
        pass

    def parse_single_file(self, path: Path, json_schema: dict) -> dict:
        if path.exists():
            try:
                return self._parse_file(path, json_schema)
            except Exception as e:
                self.config.add_error(path, e)

        return {}

    def parse_schema_object_files(self, object_type: str, json_schema: dict):
        for path in self.base_path.glob(f"*/*/{object_type}/*.yaml"):
            database = path.parents[2].name
            schema = path.parents[1].name

            try:
                yield ParsedFile(
                    path=path,
                    name=path.stem,
                    params=self._parse_file(path, json_schema),
                    database=database,
                    schema=schema,
                )
            except Exception as e:
                self.config.add_error(path, e)

    def build_complex_ident_from_str(self, object_name, context_database_name=None, context_schema_name=None) -> ComplexIdentWithPrefix:
        # Function or procedure identifier with arguments
        if object_name.endswith(')'):
            object_name, data_types_str = object_name.rstrip(')').split('(')
            data_types = [BaseDataType[dt.strip(' ')] for dt in data_types_str.split(',')] if data_types_str else []
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

    def normalise_params_dict(self, params):
        if params is None:
            return None

        if isinstance(params, dict):
            return {k.upper(): v for k, v in params.items()}

        raise ValueError(f"Value is neither None, nor dictionary [{params}]")

    def _parse_file(self, file_path: Path, json_schema: dict):
        with file_path.open('r') as f:
            data = safe_load(f) or {}
            validate(data, json_schema)

            return data


@dataclass
class ParsedFile:
    path: Path
    name: str
    params: dict
    database: Optional[str]
    schema: Optional[str]
