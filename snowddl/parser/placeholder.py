from pathlib import Path

from snowddl.config import SnowDDLConfig
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


placeholder_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": ["boolean", "number", "string"]
    }
}


class PlaceholderParser(AbstractParser):
    def __init__(self, config: SnowDDLConfig, base_path: Path, placeholder_path: Path = None):
        super().__init__(config, base_path)
        self.placeholder_path = placeholder_path

    def load_blueprints(self):
        # ENV_PREFIX placeholder is added automatically and always available
        self.config.add_placeholder('ENV_PREFIX', self.env_prefix)

        # Add other placeholders from file
        self.parse_single_file(self.base_path / 'placeholder.yaml', placeholder_json_schema, self.process_placeholder)

    def process_placeholder(self, f: ParsedFile):
        placeholders = f.params

        if self.placeholder_path:
            overloaded_placeholders = self.parse_single_file(self.placeholder_path, placeholder_json_schema)
            placeholders.update(overloaded_placeholders)

        for name, value in placeholders.items():
            name = str(name).upper()
            self.config.add_placeholder(name, value)
