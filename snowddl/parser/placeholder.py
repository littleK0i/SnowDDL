from pathlib import Path
from typing import Dict, Optional

from snowddl.blueprint import DatabaseIdent
from snowddl.parser.abc_parser import AbstractParser


# fmt: off
placeholder_json_schema = {
    "type": "object",
    "additionalProperties": {
        "anyOf": [
            {
                "type": ["boolean", "number", "string"]
            },
            {
                "type": "array",
                "items": {
                    "type": ["boolean", "number", "string"]
                },
            },
        ]
    }
}
# fmt: on


class PlaceholderParser(AbstractParser):
    def load_blueprints(self):
        # This is a special parser that does not load any blueprints, but it loads placeholders instead
        pass

    def load_placeholders(
        self, placeholder_path: Optional[Path] = None, placeholder_values: Optional[Dict] = None, args: Optional[Dict] = None
    ):
        # 1) Start with standard placeholders, always available
        placeholders = {
            "ENV_PREFIX": self.env_prefix,
        }

        if args and args.get("target_db"):
            placeholders["TARGET_DB"] = str(DatabaseIdent(self.env_prefix, args.get("target_db")))

        # 2) Merge with placeholders from normal config file
        placeholders.update(self.normalise_params_dict(self.parse_single_entity_file("placeholder", placeholder_json_schema)))

        # 3) Merge with placeholders from override config file
        if placeholder_path:
            placeholders.update(self.normalise_params_dict(self.parse_external_file(placeholder_path, placeholder_json_schema)))

        # 4) Merge with explicit placeholder values
        if placeholder_values:
            placeholders.update(self.normalise_params_dict(placeholder_values))

        for name, value in placeholders.items():
            self.config.add_placeholder(name, value)
