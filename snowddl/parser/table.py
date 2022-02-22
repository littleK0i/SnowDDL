from pathlib import Path
from re import compile, IGNORECASE

from snowddl.blueprint import TableBlueprint, TableColumn, PrimaryKeyBlueprint, UniqueKeyBlueprint, ForeignKeyBlueprint, DataType, Ident, IdentWithPrefix, ComplexIdentWithPrefix
from snowddl.config import SnowDDLConfig
from snowddl.parser.abc_parser import AbstractParser, ParsedFile
from snowddl.parser.schema import database_json_schema, schema_json_schema

col_type_re = compile(r'^(?P<type>[a-z0-9_]+(\((\d+)(,(\d+))?\))?)'
                      r'(?P<not_null> NOT NULL)?$'
                      , IGNORECASE)


table_json_schema = {
    "type": "object",
    "properties": {
        "columns": {
            "type": "object",
            "minItems": 1,
            "items": {
                "anyOf": [
                    {
                        "type": "string"
                    },
                    {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string"
                            },
                            "default": {
                                "type": "string"
                            },
                            "default_sequence": {
                                "type": "string"
                            },
                            "comment": {
                                "type": "string"
                            }
                        },
                        "required": ["type"],
                        "additionalProperties": False
                    }
                ]
            }
        },
        "cluster_by": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "change_tracking": {
            "type": "boolean"
        },
        "search_optimization": {
            "type": "boolean"
        },
        "comment": {
            "type": "string"
        },
        "primary_key": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "unique_keys": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
            }
        },
        "foreign_keys": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "columns": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    },
                    "ref_table": {
                        "type": "string"
                    },
                    "ref_columns": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    }
                },
                "additionalProperties": False
            },
            "minItems": 1
        }
    },
    "additionalProperties": False
}


class TableParser(AbstractParser):
    def __init__(self, config: SnowDDLConfig, base_path: Path):
        super().__init__(config, base_path)
        self.combined_params = self.init_combined_params()

    def init_combined_params(self):
        combined_params = {}

        for database_path in self.base_path.iterdir():
            if not database_path.is_dir():
                continue

            database_params = self.parse_single_file(database_path / 'params.yaml', database_json_schema)
            combined_params[database_path.name] = {}

            for schema_path in database_path.iterdir():
                if not schema_path.is_dir():
                    continue

                schema_params = self.parse_single_file(schema_path / 'params.yaml', schema_json_schema)

                combined_params[database_path.name][schema_path.name] = {
                    "is_transient": database_params.get('is_transient', False) or schema_params.get('is_transient', False),
                    "retention_time": schema_params.get("retention_time"),
                }

        return combined_params

    def load_blueprints(self):
        self.parse_schema_object_files('table', table_json_schema, self.process_table)

    def process_table(self, f: ParsedFile):
        column_blueprints = []

        for col_name, col in f.params['columns'].items():

            # Short syntax
            if isinstance(col, str):
                col = {
                    "type": col
                }

            m = col_type_re.match(col['type'])

            if not m:
                raise ValueError(f"Incorrect short syntax for column [{col_name}] in table [{f.database}.{f.schema}.{f.name}]: {col['type']}")

            # Default for sequence
            if col.get('default_sequence'):
                col_default = f"{self.config.build_complex_ident(col['default_sequence'], f.database, f.schema)}.NEXTVAL"
            else:
                col_default = col.get('default')

            column_blueprints.append(
                TableColumn(
                    name=Ident(col_name),
                    type=DataType(m.group('type')),
                    not_null=bool(m.group('not_null')),
                    default=col_default,
                    comment=col.get('comment'),
                )
            )

        bp = TableBlueprint(
            full_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, f.name),
            database=IdentWithPrefix(self.env_prefix, f.database),
            schema=Ident(f.schema),
            name=Ident(f.name),
            columns=column_blueprints,
            cluster_by=f.params.get('cluster_by', None),
            is_transient=f.params.get('is_transient', self.combined_params[f.database][f.schema].get('is_transient', False)),
            retention_time=f.params.get('retention_time', self.combined_params[f.database][f.schema].get('retention_time', None)),
            change_tracking=f.params.get('change_tracking', False),
            search_optimization=f.params.get('search_optimization', False),
            comment=f.params.get('comment'),
        )

        self.config.add_blueprint(bp)

        # Constraints

        if f.params.get('primary_key'):
            bp = PrimaryKeyBlueprint(
                full_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, f.name),
                table_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, f.name),
                columns=[Ident(c) for c in f.params.get('primary_key')],
                comment=None,
            )

            self.config.add_blueprint(bp)

        for columns in f.params.get('unique_keys', []):
            uk_constraint_name = f"{f.name}({','.join(columns)})"

            bp = UniqueKeyBlueprint(
                full_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, uk_constraint_name),
                table_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, f.name),
                columns=[Ident(c) for c in columns],
                comment=None,
            )

            self.config.add_blueprint(bp)

        for fk in f.params.get('foreign_keys', []):
            fk_constraint_name = f"{f.name}({','.join(fk['columns'])})"

            bp = ForeignKeyBlueprint(
                full_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, fk_constraint_name),
                table_name=ComplexIdentWithPrefix(self.env_prefix, f.database, f.schema, f.name),
                columns=[Ident(c) for c in fk['columns']],
                ref_table_name=self.config.build_complex_ident(fk['ref_table'], f.database, f.schema),
                ref_columns=[Ident(c) for c in fk['ref_columns']],
                comment=None,
            )

            self.config.add_blueprint(bp)
