from snowddl.blueprint import Grant, BusinessRoleBlueprint, IdentWithPrefix, Ident, ObjectType
from snowddl.parser.abc_parser import AbstractParser


business_role_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "schema_owner": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "schema_read": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "schema_write": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "warehouse_usage": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "warehouse_monitor": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "tech_roles": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "global_roles": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "comment": {
                "type": "string"
            }
        }
    }
}


class BusinessRoleParser(AbstractParser):
    def load_blueprints(self):
        business_role_config = self.parse_single_file(self.base_path / 'business_role.yaml', business_role_json_schema)

        for business_role_name, business_role in business_role_config.items():
            business_role_ident = self.config.build_role_ident(business_role_name, self.config.BUSINESS_ROLE_SUFFIX)

            grants = []

            for full_schema_name in business_role.get('schema_owner', []):
                grants.append(self.build_schema_role_grant(full_schema_name, 'OWNER'))

            for full_schema_name in business_role.get('schema_read', []):
                grants.append(self.build_schema_role_grant(full_schema_name, 'READ'))

            for full_schema_name in business_role.get('schema_write', []):
                grants.append(self.build_schema_role_grant(full_schema_name, 'WRITE'))

            for warehouse_name in business_role.get('warehouse_usage', []):
                grants.append(self.build_warehouse_role_grant(warehouse_name, 'USAGE'))

            for warehouse_name in business_role.get('warehouse_monitor', []):
                grants.append(self.build_warehouse_role_grant(warehouse_name, 'MONITOR'))

            for tech_role_name in business_role.get('tech_roles', []):
                grants.append(Grant(
                    privilege="USAGE",
                    on=ObjectType.ROLE,
                    name=self.config.build_role_ident(tech_role_name, self.config.TECH_ROLE_SUFFIX),
                ))

            for global_role_name in business_role.get('global_roles', []):
                grants.append(Grant(
                    privilege="USAGE",
                    on=ObjectType.ROLE,
                    name=Ident(global_role_name),
                ))

            bp = BusinessRoleBlueprint(
                full_name=business_role_ident,
                grants=grants,
                future_grants=[],
                comment=business_role.get('comment'),
            )

            self.config.add_blueprint(bp)

    def build_schema_role_grant(self, full_schema_name, grant_type):
        database, schema = full_schema_name.split('.')

        return Grant(
            privilege="USAGE",
            on=ObjectType.ROLE,
            name=self.config.build_role_ident(database, schema, grant_type, self.config.SCHEMA_ROLE_SUFFIX),
        )

    def build_warehouse_role_grant(self, warehouse_name, grant_type):
        return Grant(
            privilege="USAGE",
            on=ObjectType.ROLE,
            name=self.config.build_role_ident(warehouse_name, grant_type, self.config.WAREHOUSE_ROLE_SUFFIX),
        )
