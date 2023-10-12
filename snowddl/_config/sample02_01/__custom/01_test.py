from snowddl import DataType, Ident, TableBlueprint, TableColumn, SchemaObjectIdent, SnowDDLConfig


def handler(config: SnowDDLConfig):
    # Add custom tables
    for i in range(1,5):
        bp = TableBlueprint(
            full_name=SchemaObjectIdent(config.env_prefix, "test_db", "test_schema", f"custom_table_{i}"),
            columns=[
                TableColumn(
                    name=Ident("id"),
                    type=DataType("NUMBER(38,0)"),
                ),
                TableColumn(
                    name=Ident("name"),
                    type=DataType("VARCHAR(255)"),
                ),
            ],
            is_transient=True,
            comment=f"This table was created programmatically",
        )

        config.add_blueprint(bp)
