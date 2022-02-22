from jsonschema import validate
from pathlib import Path
from re import compile, IGNORECASE
from typing import TYPE_CHECKING
from yaml import safe_load

if TYPE_CHECKING:
    from snowddl.parser.abc_parser import AbstractParser

class ParsedFile:
    placeholder_start = '${{ '
    placeholder_end = ' }}'
    placeholder_re = compile(r'\${{\s([a-z0-9._-]+)\s}}', IGNORECASE)

    def __init__(self, parser: "AbstractParser", path: Path, json_schema: dict):
        self.parser = parser

        self.path = path
        self.name = path.stem
        self.json_schema = json_schema

        self.database = None
        self.schema = None

        if self.path.is_relative_to(parser.base_path):
            relative_path = path.relative_to(parser.base_path)

            if len(relative_path.parts) > 1:
                self.database = relative_path.parts[0]

            if len(relative_path.parts) > 2:
                self.schema = relative_path.parts[1]

        self.params = self._load_params()

        self._apply_placeholders(self.params)
        self._validate_json_schema()

    def _load_params(self):
        with self.path.open('r') as f:
            return safe_load(f) or {}

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
