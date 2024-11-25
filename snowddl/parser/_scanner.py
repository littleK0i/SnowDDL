from collections import defaultdict
from pathlib import Path
from typing import Dict, Optional, Set


class DirectoryScanner:
    allowed_file_suffixes = (".yml", ".yaml")
    allowed_file_levels = (1, 2, 3, 4)

    def __init__(self, base_path: Path):
        self.base_path = base_path

        # Key is relative path without suffix
        self.all_file_paths: Dict[str, Path] = {}
        self.accessed_files: Set[str] = set()

        # Key is database name
        self.database_dir_paths: Dict[str, Path] = {}

        # Key 1st level -> database name, 2nd level -> schema name
        self.schema_dir_paths: Dict[str, Dict[str, Path]] = defaultdict(dict)

        # Key 1st level -> object type, 2nd level -> relative path without suffix
        self.schema_object_file_paths: Dict[str, Dict[str, Path]] = defaultdict(dict)

        self._scan_dir_recursively(base_path)

    def get_database_dir_paths(self) -> Dict[str, Path]:
        return self.database_dir_paths

    def get_schema_dir_paths(self, database_key) -> Dict[str, Path]:
        return self.schema_dir_paths[self._normalise_key(database_key)]

    def get_single_file_path(self, file_key: str) -> Optional[Path]:
        file_key = self._normalise_key(file_key)

        if file_key in self.all_file_paths:
            self.accessed_files.add(file_key)
            return self.all_file_paths[file_key]

        return None

    def get_schema_object_file_paths(self, object_type: str) -> Dict[str, Path]:
        schema_object_file_paths = self.schema_object_file_paths.get(object_type, {})

        for file_key in schema_object_file_paths:
            self.accessed_files.add(file_key)

        return schema_object_file_paths

    def get_unused_file_paths(self) -> Dict[str, Path]:
        return {file_key: file_path for file_key, file_path in self.all_file_paths.items() if file_key not in self.accessed_files}

    def _scan_dir_recursively(self, dir_path: Path):
        for item_path in sorted(dir_path.iterdir()):
            relative_item_path = item_path.relative_to(self.base_path)
            relative_item_level = len(relative_item_path.parts)

            if relative_item_path.parts[0].startswith("__"):
                # Skip special directories and all items inside
                continue

            if item_path.is_dir():
                # 1st level dir is database
                if relative_item_level == 1:
                    database_key = self._normalise_key(relative_item_path.parts[0])

                    if database_key in self.database_dir_paths:
                        raise ValueError(
                            f"Detected config database directories with similar names: "
                            f"[{item_path}] and [{self.database_dir_paths[database_key]}]"
                        )

                    self.database_dir_paths[database_key] = item_path

                # 2nd level dir is schema
                if relative_item_level == 2:
                    database_key = self._normalise_key(relative_item_path.parts[0])
                    schema_key = self._normalise_key(relative_item_path.parts[1])

                    if database_key in self.schema_dir_paths and schema_key in self.schema_dir_paths[database_key]:
                        raise ValueError(
                            f"Detected config schema directories with similar names: "
                            f"[{item_path}] and [{self.schema_dir_paths[database_key][schema_key]}]"
                        )

                    self.schema_dir_paths[database_key][schema_key] = item_path

                self._scan_dir_recursively(item_path)

            if item_path.is_file():
                # Skip files with extensions other than YML / YAML
                if item_path.suffix not in self.allowed_file_suffixes:
                    continue

                # Skip files outside levels between 1st and 4th
                if relative_item_level not in self.allowed_file_levels:
                    continue

                file_key = self._normalise_key(relative_item_path.with_suffix("").as_posix())

                if file_key in self.all_file_paths:
                    raise ValueError(
                        f"Detected config files with similar names: " f"[{item_path}] and [{self.all_file_paths[file_key]}]"
                    )

                if relative_item_level == 4:
                    object_type = self._normalise_key(relative_item_path.parts[2])
                    self.schema_object_file_paths[object_type][file_key] = item_path

                self.all_file_paths[file_key] = item_path

    def _normalise_key(self, key: str):
        return key.lower()
