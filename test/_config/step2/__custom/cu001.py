from snowddl import DataType, Ident, SchemaObjectIdent, SnowDDLConfig, TableBlueprint, TableColumn, ViewBlueprint


def handler(config: SnowDDLConfig):
    # Add some custom tables and corresponding views
    for i in range(1,4):
        bp = TableBlueprint(
            full_name=SchemaObjectIdent(config.env_prefix, "db1", "sc1", f"cu001_tb{i}"),
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

        bp = ViewBlueprint(
            full_name=SchemaObjectIdent(config.env_prefix, "db1", "sc1", f"cu001_vw{i}"),
            text=f"SELECT id, name FROM cu001_tb{i}",
            comment=f"This view was created programmatically",
        )

        config.add_blueprint(bp)
