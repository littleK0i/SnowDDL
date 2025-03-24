from snowddl.blueprint import (
    AccountGrant,
    AccountObjectIdent,
    DatabaseBlueprint,
    DatabaseIdent,
    Ident,
    IdentPattern,
    build_share_read_ident,
)
from snowddl.parser.abc_parser import AbstractParser


# fmt: off
database_json_schema = {
    "type": "object",
    "properties": {
        "permission_model": {
            "type": "string",
        },
        "is_transient": {
            "type": "boolean"
        },
        "retention_time": {
            "type": "integer"
        },
        "is_sandbox": {
            "type": "boolean"
        },
        "owner_database_read": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "owner_database_write": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "owner_schema_read": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "owner_schema_write": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "owner_share_read": {
            "share_read": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
        },
        "owner_integration_usage": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "owner_warehouse_usage": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "owner_account_grants": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "owner_global_roles": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "comment": {
            "type": "string"
        }
    },
    "additionalProperties": False
}
# fmt: on


class DatabaseParser(AbstractParser):
    def load_blueprints(self):
        for database_name in self.get_database_names():
            database_params = self.parse_single_entity_file(f"{database_name}/params", database_json_schema)
            database_permission_model_name = database_params.get("permission_model", self.config.DEFAULT_PERMISSION_MODEL).upper()

            # fmt: off
            bp = DatabaseBlueprint(
                full_name=DatabaseIdent(self.env_prefix, database_name),
                permission_model=database_permission_model_name,
                is_transient=database_params.get("is_transient", False),
                retention_time=database_params.get("retention_time", None),
                is_sandbox=database_params.get("is_sandbox", False),
                owner_database_write=[IdentPattern(p) for p in database_params.get("owner_database_write", [])],
                owner_database_read=[IdentPattern(p) for p in database_params.get("owner_database_read", [])],
                owner_schema_write=[IdentPattern(p) for p in database_params.get("owner_schema_write", [])],
                owner_schema_read=[IdentPattern(p) for p in database_params.get("owner_schema_read", [])],
                owner_integration_usage=[Ident(integration_name) for integration_name in database_params.get("owner_integration_usage", [])],
                owner_share_read=[build_share_read_ident(share_name) for share_name in database_params.get("owner_share_read", [])],
                owner_warehouse_usage=[AccountObjectIdent(self.env_prefix, warehouse_name) for warehouse_name in database_params.get("owner_warehouse_usage", [])],
                owner_account_grants=[AccountGrant(privilege=privilege) for privilege in database_params.get("owner_account_grants", [])],
                owner_global_roles=[Ident(global_role_name) for global_role_name in database_params.get("owner_global_roles", [])],
                comment=database_params.get("comment", None),
            )
            # fmt: on

            self.config.add_blueprint(bp)
