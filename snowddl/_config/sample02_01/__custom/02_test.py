from snowddl import SchemaObjectIdent, SnowDDLConfig, TableBlueprint, ViewBlueprint


def handler(config: SnowDDLConfig):
    # Add view combining all custom tables
    parts = []

    for full_name, bp in config.get_blueprints_by_type_and_pattern(TableBlueprint, "test_db.test_schema.custom_table_*").items():
        parts.append(f"SELECT id, name FROM {full_name}")

    bp = ViewBlueprint(
        full_name=SchemaObjectIdent(config.env_prefix, "test_db", "test_schema", "custom_view"),
        text="\nUNION ALL\n".join(parts),
        comment=f"This view was created programmatically",
    )

    config.add_blueprint(bp)
