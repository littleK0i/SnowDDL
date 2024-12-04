from snowddl.blueprint import (
    BusinessRoleBlueprint,
    DatabaseBlueprint,
    SchemaBlueprint,
    TechnicalRoleBlueprint,
    WarehouseBlueprint,
)
from snowddl.validator.abc_validator import AbstractValidator


class BusinessRoleValidator(AbstractValidator):
    def get_blueprints(self):
        return self.config.get_blueprints_by_type(BusinessRoleBlueprint)

    def validate_blueprint(self, bp: BusinessRoleBlueprint):
        self._validate_database_schema_patterns(bp)
        self._validate_warehouse(bp)
        self._validate_technical_roles(bp)

    def _validate_database_schema_patterns(self, bp: BusinessRoleBlueprint):
        for database_name_pattern in bp.database_owner:
            if not self.config.get_blueprints_by_type_and_pattern(DatabaseBlueprint, database_name_pattern):
                raise ValueError(
                    f"Business role [{bp.full_name}] database_owner pattern [{database_name_pattern}] "
                    f"does not match any databases"
                )

        for database_name_pattern in bp.database_write:
            if not self.config.get_blueprints_by_type_and_pattern(DatabaseBlueprint, database_name_pattern):
                raise ValueError(
                    f"Business role [{bp.full_name}] database_write pattern [{database_name_pattern}] "
                    f"does not match any databases"
                )

        for database_name_pattern in bp.database_read:
            if not self.config.get_blueprints_by_type_and_pattern(DatabaseBlueprint, database_name_pattern):
                raise ValueError(
                    f"Business role [{bp.full_name}] database_read pattern [{database_name_pattern}] "
                    f"does not match any databases"
                )

        for schema_name_pattern in bp.schema_owner:
            if not self.config.get_blueprints_by_type_and_pattern(SchemaBlueprint, schema_name_pattern):
                raise ValueError(
                    f"Business role [{bp.full_name}] schema_owner pattern [{schema_name_pattern}] " f"does not match any schemas"
                )

        for schema_name_pattern in bp.schema_write:
            if not self.config.get_blueprints_by_type_and_pattern(SchemaBlueprint, schema_name_pattern):
                raise ValueError(
                    f"Business role [{bp.full_name}] schema_write pattern [{schema_name_pattern}] " f"does not match any schemas"
                )

        for schema_name_pattern in bp.schema_read:
            if not self.config.get_blueprints_by_type_and_pattern(SchemaBlueprint, schema_name_pattern):
                raise ValueError(
                    f"Business role [{bp.full_name}] schema_read pattern [{schema_name_pattern}] " f"does not match any schemas"
                )

    def _validate_warehouse(self, bp: BusinessRoleBlueprint):
        for warehouse_name in bp.warehouse_usage:
            if warehouse_name not in self.config.get_blueprints_by_type(WarehouseBlueprint):
                raise ValueError(
                    f"Business role [{bp.full_name}] warehouse_usage references to " f"undefined warehouse [{warehouse_name}]"
                )

        for warehouse_name in bp.warehouse_monitor:
            if warehouse_name not in self.config.get_blueprints_by_type(WarehouseBlueprint):
                raise ValueError(
                    f"Business role [{bp.full_name}] warehouse_monitor references to " f"undefined warehouse [{warehouse_name}]"
                )

    def _validate_technical_roles(self, bp: BusinessRoleBlueprint):
        for technical_role_name in bp.technical_roles:
            if technical_role_name not in self.config.get_blueprints_by_type(TechnicalRoleBlueprint):
                raise ValueError(
                    f"Business role [{bp.full_name}] references to " f"undefined technical role [{technical_role_name}]"
                )
