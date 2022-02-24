from abc import ABC, abstractmethod
from dataclasses import dataclass
from json import loads
from jsonschema import validate
from pathlib import Path
from traceback import format_exc
from typing import Callable, Dict, Optional, Union

from snowddl.config import SnowDDLConfig
from snowddl.blueprint import ComplexIdentWithPrefix, ComplexIdentWithPrefixAndArgs
from snowddl.parser._parsed_file import ParsedFile


class AbstractParser(ABC):
    def __init__(self, config: SnowDDLConfig, base_path: Path):
        self.config = config
        self.base_path = base_path

        self.env_prefix = config.env_prefix

    @abstractmethod
    def load_blueprints(self):
        pass

    def parse_single_file(self, path: Path, json_schema: dict, callback: Callable[[ParsedFile],Union[None,Dict]] = None):
        if not callback:
            callback = lambda f: f.params

        if path.exists():
            try:
                file = ParsedFile(self, path, json_schema)
                return callback(file)
            except Exception as e:
                self.config.add_error(path, e, format_exc())

        return {}

    def parse_schema_object_files(self, object_type: str, json_schema: dict, callback: Callable[[ParsedFile],None]):
        for path in self.base_path.glob(f"*/*/{object_type}/*.yaml"):
            try:
                file = ParsedFile(self, path, json_schema)
                callback(file)
            except Exception as e:
                self.config.add_error(path, e, format_exc())

    def normalise_params_dict(self, params):
        if params is None:
            return None

        if isinstance(params, dict):
            return {k.upper(): v for k, v in params.items()}

        raise ValueError(f"Value is neither None, nor dictionary [{params}]")
