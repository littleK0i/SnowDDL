from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict, List, Union

from snowddl.config import SnowDDLConfig
from snowddl.blueprint import NameWithType
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
                self.config.add_error(path, e)

        return {}

    def parse_schema_object_files(self, object_type: str, json_schema: dict, callback: Callable[[ParsedFile],None]):
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

    def validate_name_with_args(self, path: Path, arguments: List[NameWithType]):
        stem_name = str(path.stem)
        args_str = ','.join([a.type.base_type.name for a in arguments]).lower()

        open_pos = stem_name.find('(')
        close_pos = stem_name.find(')')

        if open_pos == -1 or close_pos == -1:
            raise ValueError(f"File [{path}] name should have list of arguments, e.g. [{stem_name}({args_str}).yaml]")

        base_name = stem_name[:open_pos]

        if stem_name[open_pos+1:close_pos] != args_str:
            raise ValueError(f"File [{path}] name does not match list of arguments, expected [{base_name}({args_str}).yaml]")

        return base_name
