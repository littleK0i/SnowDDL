from jsonschema import validate
from pathlib import Path
from re import compile, IGNORECASE
from typing import TYPE_CHECKING
from yaml import load

from snowddl.parser._yaml import SnowDDLLoader

if TYPE_CHECKING:
    from snowddl.parser.abc_parser import AbstractParser


class ParsedFile:
    placeholder_start = "${{"
    placeholder_end = "}}"
    placeholder_re = compile(r"\${{\s?([a-z0-9._-]+)\s?}}", IGNORECASE)

    def __init__(self, parser: "AbstractParser", path: Path, json_schema: dict):
        self.parser = parser

        self.path = path
        self.name = path.stem.upper()
        self.json_schema = json_schema

        self.database = None
        self.schema = None

        self._guess_database_schema_from_path()
        self._load_params()

        self._apply_placeholders(self.params)
        self._validate_json_schema()

    def _guess_database_schema_from_path(self):
        try:
            relative_path = self.path.relative_to(self.parser.scanner.base_path)
        except ValueError:
            return

        if len(relative_path.parts) > 1:
            self.database = relative_path.parts[0].upper()

        if len(relative_path.parts) > 2:
            self.schema = relative_path.parts[1].upper()

    def _load_params(self):
        with self.path.open("r", encoding="utf-8") as f:
            self.params = load(f, Loader=SnowDDLLoader) or {}

    def _apply_placeholders(self, data: dict):
        for k, v in data.items():
            if isinstance(v, dict):
                self._apply_placeholders(v)
            elif isinstance(v, list):
                data[k] = [self._apply_placeholders_inner(i) if isinstance(i, str) else i for i in v]
            elif isinstance(v, str):
                data[k] = self._apply_placeholders_inner(v)

    def _apply_placeholders_inner(self, val: str):
        if self.placeholder_start in val:
            m = self.placeholder_re.fullmatch(val)

            if m:
                # Value is a single placeholder, return and preserve type
                return self.parser.config.get_placeholder(m.group(1).upper())
            else:
                # Value is a string with multiple placeholders or other parts, replace and return as string
                return self.placeholder_re.sub(lambda m: str(self.parser.config.get_placeholder(m.group(1).upper())), val)

        return val

    def _validate_json_schema(self):
        validate(self.params, self.json_schema)
