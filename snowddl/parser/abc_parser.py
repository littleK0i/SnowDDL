from abc import ABC, abstractmethod
from logging import getLogger, NullHandler
from pathlib import Path
from traceback import TracebackException
from typing import Callable, Dict, List, Optional, Union

from snowddl.config import SnowDDLConfig
from snowddl.blueprint import BaseDataType, NameWithType
from snowddl.parser._parsed_file import ParsedFile
from snowddl.parser._scanner import DirectoryScanner


logger = getLogger(__name__)
logger.addHandler(NullHandler())


class AbstractParser(ABC):
    def __init__(self, config: SnowDDLConfig, scanner: DirectoryScanner):
        self.config = config
        self.scanner = scanner

        self.logger = logger
        self.errors: Dict[str, Exception] = {}

        self.env_prefix = config.env_prefix

    @abstractmethod
    def load_blueprints(self):
        pass

    def get_database_names(self):
        return [database_name.upper() for database_name in self.scanner.get_database_dir_paths()]

    def get_schema_names_in_database(self, database_name):
        return [schema_name.upper() for schema_name in self.scanner.get_schema_dir_paths(database_name)]

    def parse_single_entity_file(
        self, file_key: str, json_schema: dict, callback: Callable[[ParsedFile], Union[None, Dict]] = None
    ):
        if not callback:
            callback = lambda f: f.params

        path = self.scanner.get_single_file_path(file_key)

        if path:
            try:
                file = ParsedFile(self, path, json_schema)
                return callback(file)
            except Exception as e:
                self.add_error(e, path)

        return {}

    def parse_multi_entity_file(self, file_key: str, json_schema: dict, callback: Callable[[str, Dict], None]):
        path = self.scanner.get_single_file_path(file_key)

        if path:
            try:
                file = ParsedFile(self, path, json_schema)
            except Exception as e:
                self.add_error(e, path)
                return

            for entity_name, entity_params in file.params.items():
                try:
                    callback(entity_name, entity_params)
                except Exception as e:
                    self.add_error(e, path, entity_name)

    def parse_schema_object_files(self, object_type: str, json_schema: dict, callback: Callable[[ParsedFile], None]):
        for path in self.scanner.get_schema_object_file_paths(object_type).values():
            try:
                file = ParsedFile(self, path, json_schema)
                callback(file)
            except Exception as e:
                self.add_error(e, path)

    def parse_external_file(self, path: Path, json_schema: dict, callback: Callable[[ParsedFile], Union[None, Dict]] = None):
        if not callback:
            callback = lambda f: f.params

        if path.exists():
            try:
                file = ParsedFile(self, path, json_schema)
                return callback(file)
            except Exception as e:
                self.add_error(e, path)

        return {}

    def add_error(self, exc: Exception, path: Path, entity_name: Optional[str] = None):
        traceback = "".join(TracebackException.from_exception(exc).format())

        if entity_name:
            self.logger.warning(f"Failed to parse [{entity_name}] in config file [{path}]\n{traceback}")
            error_key = f"{path}:{entity_name}"
        else:
            self.logger.warning(f"Failed to parse config file [{path}]\n{traceback}")
            error_key = str(path)

        self.errors[error_key] = exc

    def normalise_sql_text_param(self, text: str):
        return text.lstrip(" \t\n\r").rstrip(" \t\n\r;")

    def normalise_params_list(self, params):
        if params is None:
            return None

        if isinstance(params, list):
            return [p.upper() for p in params]

        raise ValueError(f"Value is neither None, nor list [{params}]")

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
