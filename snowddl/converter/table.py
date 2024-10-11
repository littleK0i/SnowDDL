from re import compile

from snowddl.blueprint import ObjectType
from snowddl.converter.abc_converter import ConvertResult
from snowddl.converter.abc_schema_object_converter import AbstractSchemaObjectConverter
from snowddl.parser.sequence import sequence_json_schema
from snowddl.parser.table import table_json_schema


cluster_by_syntax_re = compile(r"^(\w+)?\((.*)\)$")
collate_type_syntax_re = compile(r"^(.*) COLLATE \'(.*)\'$")
identity_re = compile(r"^IDENTITY START (\d+) INCREMENT (\d+) (ORDER|NOORDER)$")


class TableConverter(AbstractSchemaObjectConverter):
    def get_object_type(self) -> ObjectType:
        return ObjectType.TABLE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW TABLES IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            # Skip other table types
            if (
                r.get("is_external") == "Y"
                or r.get("is_event") == "Y"
                or r.get("is_hybrid") == "Y"
                or r.get("is_iceberg") == "Y"
                or r.get("is_dynamic") == "Y"
            ):
                continue

            full_name = f"{r['database_name']}.{r['schema_name']}.{r['name']}"
            existing_objects[full_name] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "owner": r["owner"],
                "is_transient": r["kind"] == "TRANSIENT",
                "cluster_by": r["cluster_by"] if r["cluster_by"] else None,
                "change_tracking": bool(r["change_tracking"] == "ON"),
                "search_optimization": bool(r.get("search_optimization") == "ON"),
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def dump_object(self, row):
        cols, identities = self._get_columns(row)

        data = {"columns": cols}

        if row["is_transient"]:
            data["is_transient"] = True

        if row["cluster_by"]:
            data["cluster_by"] = cluster_by_syntax_re.sub(r"\2", row["cluster_by"]).split(", ")

        if row["change_tracking"]:
            data["change_tracking"] = True

        if row["search_optimization"]:
            data["search_optimization"] = True

        data["comment"] = row["comment"]

        data["primary_key"] = self._get_primary_key(row)
        data["unique_keys"] = self._get_unique_keys(row)
        data["foreign_keys"] = self._get_foreign_keys(row)

        object_path = (
            self.base_path / self._normalise_name_with_prefix(row["database"]) / self._normalise_name(row["schema"]) / "table"
        )

        self._dump_file(object_path / f"{self._normalise_name(row['name'])}.yaml", data, table_json_schema)

        for sequence_name, sequence_data in identities.items():
            object_path = (
                self.base_path
                / self._normalise_name_with_prefix(row["database"])
                / self._normalise_name(row["schema"])
                / "sequence"
            )
            object_path.mkdir(mode=0o755, parents=True, exist_ok=True)

            self._dump_file(object_path / f"{self._normalise_name(sequence_name)}.yaml", sequence_data, sequence_json_schema)

        return ConvertResult.DUMP

    def _get_columns(self, row):
        cols = {}
        identities = {}

        cur = self.engine.execute_meta(
            "DESC TABLE {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        for c in cur:
            m = collate_type_syntax_re.match(c["type"])

            if m:
                col = {
                    "type": m.group(1),
                    "collate": m.group(2),
                }
            else:
                col = {"type": c["type"]}

            if c["null?"] == "N":
                col["type"] = f"{col['type']} NOT NULL"

            if c["default"]:
                i = identity_re.match(c["default"])

                if i:
                    sequence_name = self._get_auto_sequence_name(row["name"], c["name"])
                    col["default_sequence"] = sequence_name

                    identities[sequence_name] = {
                        "start": int(i.group(1)),
                        "interval": int(i.group(2)),
                        "is_ordered": i.group(3) == "ORDER",
                    }
                elif str(c["default"]).upper().endswith(".NEXTVAL"):
                    col["default_sequence"] = self._normalise_name_with_prefix(str(c["default"])[:-8])
                else:
                    col["default"] = str(c["default"])

            if c["expression"]:
                col["expression"] = c["expression"]

            if c["comment"]:
                col["comment"] = c["comment"]

            cols[self._normalise_name(c["name"])] = col

        return cols, identities

    def _get_primary_key(self, row):
        constraints = {}

        cur = self.engine.execute_meta(
            "SHOW PRIMARY KEYS IN TABLE {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        for r in cur:
            if r["constraint_name"] not in constraints:
                constraints[r["constraint_name"]] = {}

            constraints[r["constraint_name"]][r["key_sequence"]] = r["column_name"]

        if not constraints:
            return None

        # It is possible to have multiple PRIMARY KEYS in some cases
        # Return only the first key
        for pk in constraints.values():
            return [self._normalise_name(pk[seq]) for seq in sorted(pk)]

    def _get_unique_keys(self, row):
        constraints = {}
        unique_keys = []

        cur = self.engine.execute_meta(
            "SHOW UNIQUE KEYS IN TABLE {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        for r in cur:
            if r["constraint_name"] not in constraints:
                constraints[r["constraint_name"]] = {}

            constraints[r["constraint_name"]][r["key_sequence"]] = r["column_name"]

        if not constraints:
            return None

        for uq in constraints.values():
            unique_keys.append([self._normalise_name(uq[seq]) for seq in sorted(uq)])

        return unique_keys

    def _get_foreign_keys(self, row):
        constraints = {}
        foreign_keys = []

        cur = self.engine.execute_meta(
            "SHOW IMPORTED KEYS IN TABLE {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        for r in cur:
            if r["fk_name"] not in constraints:
                constraints[r["fk_name"]] = {
                    "columns": {},
                    "ref_table": f"{r['pk_database_name']}.{r['pk_schema_name']}.{r['pk_table_name']}",
                    "ref_columns": {},
                }

            constraints[r["fk_name"]]["columns"][r["key_sequence"]] = r["fk_column_name"]
            constraints[r["fk_name"]]["ref_columns"][r["key_sequence"]] = r["pk_column_name"]

        if not constraints:
            return None

        for fk in constraints.values():
            foreign_keys.append(
                {
                    "columns": [self._normalise_name(fk["columns"][seq]) for seq in sorted(fk["columns"])],
                    "ref_table": self._normalise_name_with_prefix(fk["ref_table"]),
                    "ref_columns": [self._normalise_name(fk["ref_columns"][seq]) for seq in sorted(fk["ref_columns"])],
                }
            )

        return foreign_keys

    def _get_auto_sequence_name(self, table_name, column_name):
        return self._normalise_name_with_prefix(f"{table_name}_{column_name}_seq")
