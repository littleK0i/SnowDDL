from snowddl import *
from abc_test import AbstractTest


class TestTable(AbstractTest):
    def get_resolver_sequence(self):
        return [
            DatabaseResolver,
            SchemaResolver,
            SequenceResolver,
            TableResolver,
        ]

    def get_columns(self, engine: SnowDDLEngine, bp: TableBlueprint):
        cur = engine.execute_meta("DESC TABLE {full_name:i}", {
            "full_name": bp.full_name,
        })

        return [c for c in cur]

    def test_drop_table(self, engine):
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)

        engine.config.blueprints[TableBlueprint] = {}
        self.resolve_objects(engine)

        cur = engine.execute_meta("SHOW TABLES IN SCHEMA {full_name:i}", {
            "full_name": SchemaIdent(table_bp.full_name.env_prefix, table_bp.full_name.database, table_bp.full_name.schema)
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
                expression=None,
                collate=None,
                comment=None,
            )
        )

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        assert len(table_bp.columns) == len(self.get_columns(engine, table_bp))

    def test_drop_col(self, engine):
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)
        original_col_count = len(table_bp.columns)

        # Remove second columns
        table_bp.columns.pop(1)
        modified_col_count = len(table_bp.columns)

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        assert modified_col_count < original_col_count
        assert modified_col_count == len(self.get_columns(engine, table_bp))

    def test_alter_column_default_sequence(self, engine):
        # Create sequences
        seq_bp_1 = self.base_sequence_bp(engine.config, self.test_db, self.test_sc, "seq1")
        seq_bp_2 = self.base_sequence_bp(engine.config, self.test_db, self.test_sc, "seq2")

        # Create table with sequence 1 as default
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, "seq_table")
        table_bp.columns[0].default = f"{seq_bp_1.full_name}.NEXTVAL"

        engine.config.add_blueprint(seq_bp_1)
        engine.config.add_blueprint(seq_bp_2)
        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        assert self.get_columns(engine, table_bp)[0]['default'] == table_bp.columns[0].default

        # Change default to another sequence
        table_bp.columns[0].default = f"{seq_bp_2.full_name}.NEXTVAL"

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        assert self.get_columns(engine, table_bp)[0]['default'] == table_bp.columns[0].default

        # Drop default
        table_bp.columns[0].default = None

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        assert self.get_columns(engine, table_bp)[0]['default'] is None

    def test_alter_column_not_null(self, engine):
        # Add NOT NULL constraint
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)
        table_bp.columns[0].not_null = True

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        assert self.get_columns(engine, table_bp)[0]['null?'] == 'N'

        # Remove NOT NULL constraint
        table_bp.columns[0].not_null = False

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        assert self.get_columns(engine, table_bp)[0]['null?'] == 'Y'

    def test_alter_column_varchar_length(self, engine):
        # Increase varchar length from 10 to 20
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)
        table_bp.columns[7].type = DataType("VARCHAR(20)")

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        assert self.get_columns(engine, table_bp)[7]['type'] == "VARCHAR(20)"

        # Decrease of varchar length is not supported by Snowflake
        table_bp.columns[7].type = DataType("VARCHAR(15)")

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        # Still 20
        assert self.get_columns(engine, table_bp)[7]['type'] == "VARCHAR(20)"

    def test_alter_column_number_precision(self, engine):
        # Increase number precision from 10 to 20
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)
        table_bp.columns[0].type = DataType("NUMBER(20,0)")

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        assert self.get_columns(engine, table_bp)[0]['type'] == "NUMBER(20,0)"

        # Increase number precision from 20 to 15
        table_bp.columns[0].type = DataType("NUMBER(15,0)")

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        assert self.get_columns(engine, table_bp)[0]['type'] == "NUMBER(15,0)"

    def test_alter_column_number_scale(self, engine):
        # Change of scale is not supported by Snowflake
        table_bp = self.base_table_bp(engine.config, self.test_db, self.test_sc, self.test_table)
        table_bp.columns[0].type = DataType("NUMBER(10,2)")

        engine.config.add_blueprint(table_bp)
        self.resolve_objects(engine)

        assert self.get_columns(engine, table_bp)[0]['type'] == "NUMBER(10,0)"

    def base_sequence_bp(self, config: SnowDDLConfig, database_name, schema_name, sequence_name):
        return SequenceBlueprint(
            full_name=SchemaObjectIdent(config.env_prefix, database_name, schema_name, sequence_name),
            start=1,
            interval=1,
            comment=None,
        )
