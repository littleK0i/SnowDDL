from snowddl.blueprint import BusinessRoleBlueprint, RoleBlueprint
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver


class BusinessRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.BUSINESS_ROLE_SUFFIX

    def get_blueprints(self):
        return {
            full_name: self.transform_blueprint(business_role_bp)
            for full_name, business_role_bp in self.config.get_blueprints_by_type(BusinessRoleBlueprint).items()
        }

    def transform_blueprint(self, business_role_bp: BusinessRoleBlueprint) -> RoleBlueprint:
        grants = []

        # Database roles
        for database_name_pattern in business_role_bp.database_owner:
            grants.extend(self.build_database_role_grants(database_name_pattern, self.config.OWNER_ROLE_TYPE))

        for database_name_pattern in business_role_bp.database_write:
            grants.extend(self.build_database_role_grants(database_name_pattern, self.config.WRITE_ROLE_TYPE))

        for database_name_pattern in business_role_bp.database_read:
            grants.extend(self.build_database_role_grants(database_name_pattern, self.config.READ_ROLE_TYPE))

        # Schema roles
        for schema_name_pattern in business_role_bp.schema_owner:
            grants.extend(self.build_schema_role_grants(schema_name_pattern, self.config.OWNER_ROLE_TYPE))

        for schema_name_pattern in business_role_bp.schema_write:
            grants.extend(self.build_schema_role_grants(schema_name_pattern, self.config.WRITE_ROLE_TYPE))

        for schema_name_pattern in business_role_bp.schema_read:
            grants.extend(self.build_schema_role_grants(schema_name_pattern, self.config.READ_ROLE_TYPE))

        # Share roles
        for share_name in business_role_bp.share_read:
            grants.append(self.build_share_read_grant(share_name))

        # Warehouse roles
        for warehouse_name in business_role_bp.warehouse_usage:
            grants.append(self.build_warehouse_role_grant(warehouse_name, self.config.USAGE_ROLE_TYPE))

        for warehouse_name in business_role_bp.warehouse_monitor:
            grants.append(self.build_warehouse_role_grant(warehouse_name, self.config.MONITOR_ROLE_TYPE))

        # Technical roles
        for technical_role_name in business_role_bp.technical_roles:
            grants.append(self.build_technical_role_grant(technical_role_name))

        # Global roles
        for global_role_name in business_role_bp.global_roles:
            grants.append(self.build_global_role_grant(global_role_name))

        return RoleBlueprint(
            full_name=business_role_bp.full_name,
            grants=grants,
            comment=business_role_bp.comment,
        )
