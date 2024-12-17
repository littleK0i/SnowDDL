from snowddl.blueprint import (
    AccountGrant,
    AccountObjectIdent,
    SchemaBlueprint,
    SchemaIdent,
    Ident,
    IdentPattern,
    build_share_read_ident,
)
from snowddl.parser.abc_parser import AbstractParser
from snowddl.parser.database import database_json_schema


# fmt: off
schema_json_schema = {
    "type": "object",
    "properties": {
        "permission_model": {
            "type": "string",
        },
        "is_sandbox": {
            "type": "boolean"
        },
        "is_transient": {
            "type": "boolean"
        },
        "retention_time": {
            "type": "integer"
        },
        "external_volume": {
            "type": "string"
        },
        "catalog": {
            "type": "string",
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


class SchemaParser(AbstractParser):
    def load_blueprints(self):
        for database_name in self.get_database_names():
            database_params = self.parse_single_entity_file(f"{database_name}/params", database_json_schema)
            database_permission_model_name = database_params.get("permission_model", self.config.DEFAULT_PERMISSION_MODEL).upper()

            for schema_name in self.get_schema_names_in_database(database_name):
                schema_params = self.parse_single_entity_file(f"{database_name}/{schema_name}/params", schema_json_schema)
                schema_permission_model_name = schema_params.get("permission_model", database_permission_model_name).upper()

                combined_params = {
                    "is_transient": database_params.get("is_transient", False) or schema_params.get("is_transient", False),
                    "retention_time": schema_params.get("retention_time"),
                    "is_sandbox": schema_params.get("is_sandbox", database_params.get("is_sandbox", False)),
                }

                # fmt: off
                bp = SchemaBlueprint(
                    full_name=SchemaIdent(self.env_prefix, database_name, schema_name),
                    permission_model=schema_permission_model_name,
                    is_sandbox=combined_params.get("is_sandbox", False),
                    is_transient=combined_params.get("is_transient", False),
                    retention_time=combined_params.get("retention_time", None),
                    external_volume=Ident(schema_params.get("external_volume")) if schema_params.get("external_volume") else None,
                    catalog=Ident(schema_params.get("catalog")) if schema_params.get("catalog") else None,
                    owner_database_write=[IdentPattern(p) for p in schema_params.get("owner_database_write", [])],
                    owner_database_read=[IdentPattern(p) for p in schema_params.get("owner_database_read", [])],
                    owner_schema_write=[IdentPattern(p) for p in schema_params.get("owner_schema_write", [])],
                    owner_schema_read=[IdentPattern(p) for p in schema_params.get("owner_schema_read", [])],
                    owner_warehouse_usage=[AccountObjectIdent(self.env_prefix, warehouse_name) for warehouse_name in schema_params.get("owner_warehouse_usage", [])],
                    owner_integration_usage=[Ident(integration_name) for integration_name in schema_params.get("owner_integration_usage", [])],
                    owner_share_read=[build_share_read_ident(share_name) for share_name in schema_params.get("owner_share_read", [])],
                    owner_account_grants=[AccountGrant(privilege=privilege) for privilege in schema_params.get("owner_account_grants", [])],
                    owner_global_roles=[Ident(global_role_name) for global_role_name in schema_params.get("owner_global_roles", [])],
                    comment=schema_params.get("comment", None),
                )
                # fmt: on

                self.config.add_blueprint(bp)
