from snowddl import DataType, Ident, SchemaObjectIdent, SnowDDLConfig, TableBlueprint, TableColumn


def handler(config: SnowDDLConfig):
    for table_num in range(1, 10001):
        bp = TableBlueprint(
            full_name=SchemaObjectIdent(config.env_prefix, "db1", f"sc1", f"table_{table_num}"),
            columns=[
                TableColumn(
                    name=Ident("id"),
                    type=DataType("NUMBER(38,0)"),
                ),
                TableColumn(
                    name=Ident("name"),
                    type=DataType("VARCHAR(255)"),
                ),
                TableColumn(
                    name=Ident("status"),
                    type=DataType("VARCHAR(255)"),
                ),
            ],
            is_transient=True,
        )

        config.add_blueprint(bp)
