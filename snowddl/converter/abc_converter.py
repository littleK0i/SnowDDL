from abc import ABC, abstractmethod
from enum import Enum
from concurrent.futures import as_completed
from jsonschema import validate
from pathlib import Path
from traceback import format_exc
from typing import Dict, List, TYPE_CHECKING
from yaml import dump_all

from snowddl.error import SnowDDLExecuteError
from snowddl.blueprint import ObjectType, Edition
from snowddl.converter._yaml import SnowDDLDumper, YamlFoldedStr, YamlLiteralStr

if TYPE_CHECKING:
    from snowddl.engine import SnowDDLEngine


class ConvertResult(Enum):
    DUMP = "DUMP"
    EMPTY = "EMPTY"
    SKIP = "SKIP"
    ERROR = "ERROR"


class AbstractConverter(ABC):
    skip_min_edition = Edition.STANDARD

    def __init__(self, engine: "SnowDDLEngine", base_path: Path):
        self.engine = engine
        self.config = engine.config

        self.base_path = base_path
        self.env_prefix = self.config.env_prefix

        self.object_type = self.get_object_type()
        self.existing_objects: Dict[str, Dict] = {}

        self.converted_objects: Dict[ConvertResult, List[str]] = {k: [] for k in ConvertResult}
        self.errors: Dict[str, Exception] = {}

    def convert(self):
        if self._is_skipped():
            return

        try:
            self.existing_objects = self.get_existing_objects()
        except SnowDDLExecuteError as e:
            self.engine.logger.info(f"Could not get existing objects for converter [{self.__class__.__name__}]: \n{e.verbose_message()}")
            raise e.snow_exc

        tasks = {}

        for full_name in sorted(self.existing_objects):
            tasks[full_name] = (self.dump_object, self.existing_objects[full_name])

        self._process_tasks(tasks)

    def _process_tasks(self, tasks):
        futures = {}

        for full_name, args in tasks.items():
            futures[self.engine.executor.submit(*args)] = full_name

        for f in as_completed(futures):
            full_name = futures[f]

            try:
                result = f.result()
                self.engine.logger.info(f"Converted {self.object_type.name} [{full_name}]: {result.value}")
            except Exception as e:
                result = ConvertResult.ERROR

                if isinstance(e, SnowDDLExecuteError):
                    error_text = e.verbose_message()
                else:
                    error_text = format_exc()

                self.engine.logger.warning(f"Converted {self.object_type.name} [{full_name}]: {result.value}\n{error_text}")
                self.errors[full_name] = e

            self.converted_objects[result].append(full_name)

    def _is_skipped(self):
        if self.engine.context.edition < self.skip_min_edition:
            return True

        if self.object_type in self.engine.settings.exclude_object_types:
            return True

        if self.engine.settings.include_object_types:
            return not (self.object_type in self.engine.settings.include_object_types)

        return False

    def _dump_file(self, file_path: Path, data: Dict, json_schema: dict):
        # Remove None values
        data = {k:v for k,v in data.items() if v is not None}

        # Validate JSON schema
        validate(data, json_schema)

        # (Over)write file
        with file_path.open('w') as f:
            dump_all([data], f, Dumper=SnowDDLDumper, sort_keys=False)

    def _normalise_name(self, name: str):
        return name.lower()

    def _normalise_name_with_prefix(self, name: str):
        if name.startswith(self.env_prefix):
            name = name[len(self.env_prefix):]

        return self._normalise_name(name)

    @abstractmethod
    def get_object_type(self) -> ObjectType:
        pass

    @abstractmethod
    def get_existing_objects(self) -> Dict[str, Dict]:
        pass

    @abstractmethod
    def dump_object(self, row: Dict) -> ConvertResult:
        pass
