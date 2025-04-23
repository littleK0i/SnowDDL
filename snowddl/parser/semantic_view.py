from snowddl.blueprint import (
    Ident,
    SemanticViewBlueprint,
    SemanticViewExpression,
    SemanticViewRelationship,
    SemanticViewTable,
    SchemaObjectIdent,
    build_schema_object_ident,
)
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
semantic_view_json_schema = {
    "type": "object",
    "properties": {
        "tables": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "table_alias": {
                        "type": "string"
                    },
                    "table_name": {
                        "type": "string"
                    },
                    "primary_key": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    },
                    "with_synonyms": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    },
                    "comment": {
                        "type": "string"
                    },
                },
                "required": ["table_name"],
            },
            "minItems": 1
        },
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "relationship_identifier": {
                        "type": "string"
                    },
                    "table_alias": {
                        "type": "string"
                    },
                    "columns": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    },
                    "ref_table_alias": {
                        "type": "string"
                    },
                    "ref_columns": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    },
                },
                "required": ["table_alias", "columns", "ref_table_alias", "ref_columns"],
            },
            "minItems": 1
        },
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "table_alias": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "sql": {
                        "type": "string"
                    },
                    "with_synonyms": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    },
                    "comment": {
                        "type": "string"
                    },
                },
                "required": ["table_alias", "name", "sql"],
            },
            "minItems": 1
        },
        "dimensions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "table_alias": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "sql": {
                        "type": "string"
                    },
                    "with_synonyms": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    },
                    "comment": {
                        "type": "string"
                    },
                },
                "required": ["table_alias", "name", "sql"],
            },
            "minItems": 1
        },
        "metrics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "table_alias": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "sql": {
                        "type": "string"
                    },
                    "with_synonyms": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    },
                    "comment": {
                        "type": "string"
                    },
                },
                "required": ["table_alias", "name", "sql"],
            },
            "minItems": 1
        },
        "comment": {
            "type": "string"
        },
    },
    "required": ["tables"],
    "additionalProperties": False
}
# fmt: on


class SemanticViewParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files("semantic_view", semantic_view_json_schema, self.process_semantic_view)

    def process_semantic_view(self, f: ParsedFile):
        bp = SemanticViewBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            tables=[self.build_semantic_view_table(table_def, f) for table_def in f.params.get("tables", [])],
            relationships=[self.build_semantic_view_relationship(rel_def) for rel_def in f.params.get("relationships", [])],
            facts=[self.build_semantic_view_expression(expr_def) for expr_def in f.params.get("facts", [])],
            dimensions=[self.build_semantic_view_expression(expr_def) for expr_def in f.params.get("dimensions", [])],
            metrics=[self.build_semantic_view_expression(expr_def) for expr_def in f.params.get("metrics", [])],
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)

    def build_semantic_view_table(self, table_def: dict, f: ParsedFile):
        return SemanticViewTable(
            table_alias=Ident(table_def.get("table_alias")),
            table_name=build_schema_object_ident(self.env_prefix, table_def.get("table_name"), f.database, f.schema),
            primary_key=[Ident(c) for c in table_def.get("primary_key")] if table_def.get("primary_key") else None,
            with_synonyms=[s for s in table_def.get("with_synonyms")] if table_def.get("with_synonyms") else None,
            comment=table_def.get("comment"),
        )

    def build_semantic_view_relationship(self, rel_def: dict):
        return SemanticViewRelationship(
            relationship_identifier=rel_def.get("relationship_identifier"),
            table_alias=Ident(rel_def.get("table_alias")),
            columns=[Ident(c) for c in rel_def.get("columns")],
            ref_table_alias=Ident(rel_def.get("ref_table_alias")),
            ref_columns=[Ident(c) for c in rel_def.get("ref_columns")],
        )

    def build_semantic_view_expression(self, expr_def: dict):
        return SemanticViewExpression(
            table_alias=Ident(expr_def.get("table_alias")),
            name=Ident(expr_def.get("name")),
            sql=self.normalise_sql_text_param(expr_def.get("sql")),
            with_synonyms=[s for s in expr_def.get("with_synonyms")] if expr_def.get("with_synonyms") else None,
            comment=expr_def.get("comment"),
        )
