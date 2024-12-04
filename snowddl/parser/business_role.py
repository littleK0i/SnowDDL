from snowddl.blueprint import (
    AccountObjectIdent,
    BusinessRoleBlueprint,
    Ident,
    IdentPattern,
    build_role_ident,
    build_share_read_ident,
)
from snowddl.parser.abc_parser import AbstractParser


# fmt: off
business_role_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "database_owner": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "database_write": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "database_read": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "schema_owner": {
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
            "schema_read": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "share_read": {
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
            "technical_roles": {
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
        },
        "additionalProperties": False,
    }
}
# fmt: on


class BusinessRoleParser(AbstractParser):
    def load_blueprints(self):
        self.parse_multi_entity_file("business_role", business_role_json_schema, self.process_business_role)

    def process_business_role(self, business_role_name, business_role_params):
        technical_roles = []

        for technical_role_name in business_role_params.get("technical_roles", []) + business_role_params.get("tech_roles", []):
            technical_roles.append(build_role_ident(self.env_prefix, technical_role_name, self.config.TECHNICAL_ROLE_SUFFIX))

        # fmt: off
        bp = BusinessRoleBlueprint(
            full_name=build_role_ident(self.env_prefix, business_role_name, self.config.BUSINESS_ROLE_SUFFIX),
            database_owner=[IdentPattern(p) for p in business_role_params.get("database_owner", [])],
            database_write=[IdentPattern(p) for p in business_role_params.get("database_write", [])],
            database_read=[IdentPattern(p) for p in business_role_params.get("database_read", [])],
            schema_owner=[IdentPattern(p) for p in business_role_params.get("schema_owner", [])],
            schema_write=[IdentPattern(p) for p in business_role_params.get("schema_write", [])],
            schema_read=[IdentPattern(p) for p in business_role_params.get("schema_read", [])],
            share_read=[build_share_read_ident(share_name) for share_name in business_role_params.get("share_read", [])],
            warehouse_usage=[AccountObjectIdent(self.env_prefix, warehouse_name) for warehouse_name in business_role_params.get("warehouse_usage", [])],
            warehouse_monitor=[AccountObjectIdent(self.env_prefix, warehouse_name) for warehouse_name in business_role_params.get("warehouse_monitor", [])],
            technical_roles=technical_roles,
            global_roles=[Ident(global_role_name) for global_role_name in business_role_params.get("global_roles", [])],
            comment=business_role_params.get("comment"),
        )
        # fmt: on

        self.config.add_blueprint(bp)
