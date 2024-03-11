from json import loads
from pathlib import Path

from snowddl.blueprint import ObjectType, DataType, BaseDataType
from snowddl.converter.abc_converter import ConvertResult
from snowddl.converter.abc_schema_object_converter import AbstractSchemaObjectConverter
from snowddl.converter._yaml import YamlLiteralStr, YamlIncludeStr
from snowddl.parser.function import function_json_schema
from snowddl.resolver._utils import dtypes_from_arguments


class FunctionConverter(AbstractSchemaObjectConverter):
    def get_object_type(self) -> ObjectType:
        return ObjectType.FUNCTION

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW USER FUNCTIONS IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            # Skip external functions
            if r["is_external_function"] == "Y":
                continue

            full_name = f"{r['catalog_name']}.{r['schema_name']}.{r['name']}({dtypes_from_arguments(r['arguments'])})"

            existing_objects[full_name] = {
                "database": r["catalog_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "language": r["language"],
                "arguments": r["arguments"],
                "comment": r["description"] if r["description"] else None,
                "is_table_function": r["is_table_function"] == "Y",
                "is_secure": r["is_secure"] == "Y",
                "is_memoizable": r["is_memoizable"] == "Y",
            }

        return existing_objects

    def dump_object(self, row):
        dtypes = dtypes_from_arguments(row["arguments"])

        cur = self.engine.execute_meta(
            "DESC FUNCTION {database:i}.{schema:i}.{name:i}({dtypes:r})",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
                "dtypes": dtypes,
            },
        )

        desc_func_row = {r["property"]: r["value"] for r in cur}

        object_path = (
            self.base_path / self._normalise_name_with_prefix(row["database"]) / self._normalise_name(row["schema"]) / "function"
        )

        data = {
            "language": row["language"],
            "runtime_version": desc_func_row.get("runtime_version"),
            "arguments": self._get_arguments(desc_func_row),
            "returns": self._get_returns(desc_func_row),
            "is_secure": True if row["is_secure"] else None,
            "is_strict": True if desc_func_row.get("null handling") == "RETURNS NULL ON NULL INPUT" else None,
            "is_immutable": True if desc_func_row.get("volatility") == "IMMUTABLE" else None,
            "is_memoizable": True if row["is_memoizable"] else None,
            "imports": self._get_imports(desc_func_row),
            "packages": self._get_packages(desc_func_row),
            "handler": desc_func_row.get("handler"),
            "body": self._get_body_or_include(object_path, row["name"], dtypes, desc_func_row),
            "comment": row.get("comment"),
        }

        if data:
            file_name = self._normalise_name(f"{row['name']}({dtypes}).yaml")
            self._dump_file(object_path / file_name, data, function_json_schema)
            return ConvertResult.DUMP

        return ConvertResult.EMPTY

    def _get_body_or_include(self, object_path: Path, name: str, dtypes: str, desc_func_row: dict):
        if not desc_func_row.get("body"):
            return None

        body = str(desc_func_row["body"])
        language = str(desc_func_row["language"]).lower()

        if self.engine.settings.convert_function_body_to_file:
            if language == "python":
                file_ext = "py"
            elif language == "javascript":
                file_ext = "js"
            else:
                file_ext = language

            file_name = self._normalise_name(f"{name}({dtypes}).{file_ext}")
            self._dump_code(object_path / language / file_name, body)

            return YamlIncludeStr(f"{language}/{file_name}")
        else:
            return YamlLiteralStr(body)

    def _get_arguments(self, desc_func_row: dict):
        if desc_func_row["signature"] == "()":
            return None

        arguments = {}

        for part in str(desc_func_row["signature"])[1:-1].split(", "):
            name, base_dtype = part.split(" ")
            arguments[name.lower()] = str(DataType.from_base_type(BaseDataType[base_dtype]))

        return arguments

    def _get_returns(self, desc_func_row: dict):
        if str(desc_func_row["returns"]).startswith("TABLE"):
            return self._get_returns_table(desc_func_row)

        return self._get_returns_single(desc_func_row)

    def _get_returns_single(self, desc_func_row: dict):
        return str(DataType(desc_func_row["returns"]))

    def _get_returns_table(self, desc_func_row: dict):
        returns = {}

        for part in str(desc_func_row["returns"])[7:-1].split(", "):
            name, base_dtype = part.split(" ")
            returns[name.lower()] = str(DataType.from_base_type(BaseDataType[base_dtype]))

        return returns

    def _get_imports(self, desc_func_row):
        if "imports" not in desc_func_row:
            return None

        if desc_func_row["imports"] == "[]":
            return None

        imports = []

        for part in str(desc_func_row["imports"])[1:-1].split(", "):
            stage, path = part.split("/", 2)
            imports.append(
                {
                    "stage": stage[1:].lower(),
                    "path": path,
                }
            )

        return imports

    def _get_packages(self, desc_func_row):
        if "packages" not in desc_func_row:
            return None

        if desc_func_row["packages"] == "[]":
            return None

        # Snowflake uses single quotes for packages meta
        packages = loads(str(desc_func_row["packages"]).replace("'", '"'))

        return packages
