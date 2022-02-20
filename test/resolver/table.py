from snowddl import *
from abc_test import AbstractTest


class TestTable(AbstractTest):
    def test_drop_table(self, engine):
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)

        engine.config.blueprints[TableBlueprint] = {}
        self.resolve_objects(engine)

        cur = engine.execute_meta("SHOW TABLES IN {schema_name:i}", {
            "schema_name": table_bp.schema,
        })

        assert 0 == cur.rowcount

    def test_add_col(self, engine):
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)

        table_bp.columns.append(
            TableColumn(
                name=Ident("col1"),
                type=DataType("NUMBER(1,0)"),
                not_null=False,
                default=None,
                comment=None,
            )
        )

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        cur = engine.execute_meta("DESC TABLE {full_name:i}", {
            "full_name": table_bp.full_name,
        })

        assert len(table_bp.columns) == cur.rowcount

    def test_drop_col(self, engine):
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)
        original_col_count = len(table_bp.columns)

        table_bp.columns = list(filter(lambda col: col.type.base_type != BaseDataType.NUMBER, table_bp.columns))
        modified_col_count = len(table_bp.columns)

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        cur = engine.execute_meta("DESC TABLE {full_name:i}", {
            "full_name": table_bp.full_name,
        })

        assert modified_col_count < original_col_count
        assert modified_col_count == cur.rowcount
