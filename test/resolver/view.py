from snowddl import *
from abc_test import AbstractTest


class TestView(AbstractTest):
    def get_resolver_sequence(self):
        return [
            DatabaseResolver,
            SchemaResolver,
            TableResolver,
            ViewResolver,
        ]

    def get_columns(self, engine: SnowDDLEngine, bp: ViewBlueprint):
        cur = engine.execute_meta("DESC TABLE {full_name:i}", {
            "full_name": bp.full_name,
        })

        return [c for c in cur]

    def test_recreate_invalid_view(self, engine):
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)
        view_bp = self.base_view_bp(engine.config, self.test_db, self.test_sc, "TEST_VIEW")

        view_bp.text = engine.format("SELECT * FROM {table_name:i}", {
            "table_name": table_bp.full_name,
        })

        engine.config.add_blueprint(view_bp)
        self.resolve_objects(engine)

        assert len(self.get_columns(engine, table_bp)) == len(self.get_columns(engine, view_bp))

        # Re-create invalid view even if text is exactly the same
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)
        table_bp.columns.pop(1)

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        assert len(self.get_columns(engine, table_bp)) == len(self.get_columns(engine, view_bp))

    def test_some_columns_view(self, engine):
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)
        view_bp = self.base_view_bp(engine.config, self.test_db, self.test_sc, "TEST_VIEW")

        view_bp.text = engine.format("SELECT num1, var1, ntz1 FROM {table_name:i}", {
            "table_name": table_bp.full_name,
        })

        engine.config.add_blueprint(view_bp)
        self.resolve_objects(engine)

        assert 3 == len(self.get_columns(engine, view_bp))

    def test_some_columns_with_comment_view(self, engine):
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)
        view_bp = self.base_view_bp(engine.config, self.test_db, self.test_sc, "TEST_VIEW")

        view_bp.text = engine.format("SELECT num1, var1, ntz1 FROM {table_name:i}", {
            "table_name": table_bp.full_name,
        })

        view_bp.columns = [
            ViewColumn(name=Ident("num1"), comment="comment for num1"),
            ViewColumn(name=Ident("var1"), comment="comment for var1"),
            ViewColumn(name=Ident("ntz1"), comment="comment for ntz1"),
        ]

        engine.config.add_blueprint(view_bp)
        self.resolve_objects(engine)

        assert 3 == len(self.get_columns(engine, view_bp))
        assert "comment for num1" == self.get_columns(engine, view_bp)[0]['comment']

    def base_view_bp(self, config: SnowDDLConfig, database_name, schema_name, view_name):
        return ViewBlueprint(
            full_name=SchemaObjectIdent(config.env_prefix, database_name, schema_name, view_name),
            text='',
            columns=None,
            is_secure=False,
            depends_on=[],
            comment=None,
        )
