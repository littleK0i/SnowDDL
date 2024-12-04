from snowddl.blueprint import DatabaseBlueprint
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
            target_blueprints = self.config.get_blueprints_by_type_and_pattern(DatabaseBlueprint, database_name_pattern)

            if not target_blueprints:
                raise ValueError(
                    f"Database [{bp.full_name}] owner_database_write pattern [{database_name_pattern}] "
                    f"does not match any databases"
                )

            for target_bp in target_blueprints.values():
                target_db_permission_model = self.config.get_permission_model(target_bp.permission_model)

                if not target_db_permission_model.ruleset.create_database_write_role:
                    raise ValueError(
                        f"Database [{bp.full_name}] owner_database_write refers to another database [{target_bp.full_name}] "
                        f"without associated database_write role"
                    )

        for database_name_pattern in bp.owner_database_read:
            target_blueprints = self.config.get_blueprints_by_type_and_pattern(DatabaseBlueprint, database_name_pattern)

            if not target_blueprints:
                raise ValueError(
                    f"Database [{bp.full_name}] owner_database_read pattern [{database_name_pattern}] "
                    f"does not match any databases"
                )

            for target_bp in target_blueprints.values():
                target_db_permission_model = self.config.get_permission_model(target_bp.permission_model)

                if not target_db_permission_model.ruleset.create_database_read_role:
                    raise ValueError(
                        f"Database [{bp.full_name}] owner_database_read refers to another database [{target_bp.full_name}] "
                        f"without associated database_read role"
                    )
