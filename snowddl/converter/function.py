import re
import json
from pathlib import Path

from snowddl.blueprint import ObjectType
from snowddl.converter.abc_converter import ConvertResult
from snowddl.converter.abc_schema_object_converter import AbstractSchemaObjectConverter
from snowddl.converter._yaml import YamlLiteralStr
from snowddl.parser.function import function_json_schema

args_re = re.compile(r"^(.+?)\((.+?)\)")
args_type_re = re.compile(r"^.+?(\(.+?\)) ")
returns_re = re.compile(r".+?RETURN.+?\((.+?)\)")

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
            existing_objects[f"{r['catalog_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["catalog_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "language": r["language"],
                "arguments": r["arguments"],
                "comment": r["description"] if r["description"] else None,
                "table_function": r["is_table_function"] == "Y",
                "is_secure": r["is_secure"] == "Y",
                "is_external_function": r["is_external_function"] == "Y",
                "is_memoizable": r["is_memoizable"] == "Y",
            }

        return existing_objects

    def dump_object(self, row):
        args = self._get_argument_type(row["arguments"])
        cur = self.engine.execute_meta(
            "DESC FUNCTION {database:i}.{schema:i}.{name:i}" + args,
                {
                    "database": row["database"],
                    "schema": row["schema"],
                    "name": row["name"],
                }
            )

        desc_func_row = dict()
        for r in cur:
            desc_func_row[r["property"]] = r["value"]

        object_path = (
            self.base_path / self._normalise_name_with_prefix(row["database"]) / self._normalise_name(row["schema"]) / "function"
        )

        object_path.mkdir(mode=0o755, parents=True, exist_ok=True)

        data = {
            "language": row["language"].upper(),
            "arguments": self._get_arguments(row["arguments"]),
            "returns": self._get_returns(row["arguments"]),
            "handler": desc_func_row["handler"] if "handler" in desc_func_row else None,
            "body": self._get_body_or_include(object_path, row["name"], desc_func_row),
            "is_secure": row["is_secure"] == "Y" if "is_secure" in row else None,
            "is_strict": row["is_strict"] == "Y" if "is_strict" in row else None,
            "is_immutable": row["is_immutable"] == "Y" if "is_immutable" in row else None,
            "is_memoizable": row["is_memoizable"] == "Y" if "is_memoizable" in row else None,
            "runtime_version": desc_func_row["runtime_version"] 
                if "runtime_version" in desc_func_row else None,
            "imports": self._get_imports(desc_func_row),
            "packages": self._get_packages(desc_func_row),
            "external_access_integrations": None,  #TBD
            "secrets": None,  # TBD
            "comment": row["comment"] if "comment" in row else None,
        }

        if data:
            self._dump_file(object_path / f"{self._normalise_name(row['name'])}.yaml", data, function_json_schema)
            return ConvertResult.DUMP

        return ConvertResult.EMPTY

    def _get_body_or_include(self, object_path: Path, name: str, row: dict):
        if "body" not in row:
            return None
        body = row["body"]
        if self.engine.settings.add_include_files:
            dir = row["language"].lower()
            suffix = dir
            if dir == "python":
                suffix = "py"
            elif dir == "javascript":
                suffix = "js"
            file = f"{name}.{suffix}".lower()

            source_path = object_path / dir
            source_path.mkdir(mode=0o755, parents=True, exist_ok=True)
            (source_path / file).write_text(body, encoding="utf-8")

            return f"!include {dir}/{file}"
        else:
            return YamlLiteralStr(body)

    def _get_argument_type(self, full_args: str):
        return args_type_re.search(full_args).group(1)

    def _get_arguments(self, full_args: str):
        args = full_args.split(" RETURN ")[0]
        g = args_re.search(args).groups()
        return {g[0]: g[1]}

    def _get_returns(self, full_args: str):
        d = dict()
        for i in returns_re.search(full_args).group(1).split(","):
            (l, r) = i.split()
            d[l] = r
        return d

    # ['snowflake-snowpark-python']
    def _get_packages(self, row):
        if "packages" not in row:
            return None
        arr = json.loads(row["packages"])
        return arr if len(arr) > 0 else None

    def _get_imports(self, row):
        if "imports" not in row:
            return None
        arr = json.loads(row["imports"])
        return arr if len(arr) > 0 else None
