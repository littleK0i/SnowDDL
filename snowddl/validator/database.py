from snowddl.blueprint import DatabaseBlueprint, SchemaBlueprint
from snowddl.validator.abc_validator import AbstractValidator


class DatabaseValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(DatabaseBlueprint)

    def validate_blueprint(self, bp: DatabaseBlueprint):
        self._validate_owner_parameters(bp)
        self._validate_owner_patterns(bp)

    def _validate_owner_parameters(self, bp: DatabaseBlueprint):
        database_permission_model = self.config.get_permission_model(bp.permission_model)

        if not database_permission_model.ruleset.create_database_owner_role:
            if bp.owner_database_write:
                raise ValueError(
                    f"Cannot use parameter owner_database_write for database [{bp.full_name}] due to permission model ruleset"
                )

            if bp.owner_database_read:
                raise ValueError(
                    f"Cannot use parameter owner_database_read for database [{bp.full_name}] due to permission model ruleset"
                )

            if bp.owner_schema_write:
                raise ValueError(
                    f"Cannot use parameter owner_schema_write for database [{bp.full_name}] due to permission model ruleset"
                )

            if bp.owner_schema_read:
                raise ValueError(
                    f"Cannot use parameter owner_schema_read for database [{bp.full_name}] due to permission model ruleset"
                )

            if bp.owner_integration_usage:
                raise ValueError(
                    f"Cannot use parameter owner_integration_usage for database [{bp.full_name}] due to permission model ruleset"
                )

            if bp.owner_share_read:
                raise ValueError(
                    f"Cannot use parameter owner_share_read for database [{bp.full_name}] due to permission model ruleset"
                )

            if bp.owner_warehouse_usage:
                raise ValueError(
                    f"Cannot use parameter owner_warehouse_usage for database [{bp.full_name}] due to permission model ruleset"
                )

            if bp.owner_account_grants:
                raise ValueError(
                    f"Cannot use parameter owner_account_grants for database [{bp.full_name}] due to permission model ruleset"
                )

            if bp.owner_global_roles:
                raise ValueError(
                    f"Cannot use parameter owner_global_roles for database [{bp.full_name}] due to permission model ruleset"
                )

    def _validate_owner_patterns(self, bp: DatabaseBlueprint):
        for database_name_pattern in bp.owner_database_write:
            if not self.config.get_blueprints_by_type_and_pattern(DatabaseBlueprint, database_name_pattern):
                raise ValueError(
                    f"Database [{bp.full_name}] owner_database_write pattern [{database_name_pattern}] "
                    f"does not match any databases"
                )

        for database_name_pattern in bp.owner_database_read:
            if not self.config.get_blueprints_by_type_and_pattern(DatabaseBlueprint, database_name_pattern):
                raise ValueError(
                    f"Database [{bp.full_name}] owner_database_read pattern [{database_name_pattern}] "
                    f"does not match any databases"
                )

        for schema_name_pattern in bp.owner_schema_write:
            if not self.config.get_blueprints_by_type_and_pattern(SchemaBlueprint, schema_name_pattern):
                raise ValueError(
                    f"Database [{bp.full_name}] owner_schema_write pattern [{schema_name_pattern}] " f"does not match any schemas"
                )

        for schema_name_pattern in bp.owner_schema_read:
            if not self.config.get_blueprints_by_type_and_pattern(SchemaBlueprint, schema_name_pattern):
                raise ValueError(
                    f"Database [{bp.full_name}] owner_schema_read pattern [{schema_name_pattern}] " f"does not match any schemas"
                )
