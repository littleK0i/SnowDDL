from snowddl.blueprint import Grant, BusinessRoleBlueprint, AbstractIdentWithPrefix, Ident, ObjectType, SchemaBlueprint, build_role_ident
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


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
        self.parse_single_file(self.base_path / 'business_role.yaml', business_role_json_schema, self.process_business_role)

    def process_business_role(self, file: ParsedFile):
        for business_role_name, business_role in file.params.items():
            business_role_ident = build_role_ident(self.env_prefix, business_role_name, self.config.BUSINESS_ROLE_SUFFIX)

            grants = []

            for full_schema_name in business_role.get('schema_owner', []):
                grants.extend(self.build_schema_role_grants(full_schema_name, 'OWNER'))

            for full_schema_name in business_role.get('schema_read', []):
                grants.extend(self.build_schema_role_grants(full_schema_name, 'READ'))

            for full_schema_name in business_role.get('schema_write', []):
                grants.extend(self.build_schema_role_grants(full_schema_name, 'WRITE'))

            for warehouse_name in business_role.get('warehouse_usage', []):
                grants.append(self.build_warehouse_role_grant(warehouse_name, 'USAGE'))

            for warehouse_name in business_role.get('warehouse_monitor', []):
                grants.append(self.build_warehouse_role_grant(warehouse_name, 'MONITOR'))

            for tech_role_name in business_role.get('tech_roles', []):
                grants.append(Grant(
                    privilege="USAGE",
                    on=ObjectType.ROLE,
                    name=build_role_ident(self.env_prefix, tech_role_name, self.config.TECH_ROLE_SUFFIX),
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

    def build_schema_role_grants(self, full_schema_name, grant_type):
        grants = []

        for schema_bp in self.config.get_blueprints_by_type_and_pattern(SchemaBlueprint, full_schema_name).values():
            grants.append(
                Grant(
                    privilege="USAGE",
                    on=ObjectType.ROLE,
                    name=build_role_ident(self.env_prefix, schema_bp.full_name.database, schema_bp.full_name.schema, grant_type, self.config.SCHEMA_ROLE_SUFFIX),
                )
            )

        if not grants:
            raise ValueError(f"No {ObjectType.SCHEMA.plural} matched wildcard grant with pattern [{full_schema_name}]")

        return grants

    def build_warehouse_role_grant(self, warehouse_name, grant_type):
        return Grant(
            privilege="USAGE",
            on=ObjectType.ROLE,
            name=build_role_ident(self.env_prefix, warehouse_name, grant_type, self.config.WAREHOUSE_ROLE_SUFFIX),
        )
