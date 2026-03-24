from snowddl.blueprint import (
    AccountGrant,
    AccountObjectIdent,
    DatabaseBlueprint,
    DatabaseIdent,
    Ident,
    IdentPattern,
    build_schema_object_ident,
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
        "external_volume": {
            "type": "string"
        },
        "catalog": {
            "type": "string",
        },
        "catalog_sync": {
            "type": "string",
        },
        "log_level": {
            "type": "string",
            "enum": ["OFF", "FATAL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE"]
        },
        "log_event_level": {
            "type": "string",
            "enum": ["OFF", "FATAL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE"]
        },
        "metric_level": {
            "type": "string",
            "enum": ["ALL", "NONE"]
        },
        "trace_level": {
            "type": "string",
            "enum": ["OFF", "ON_EVENT", "ALWAYS"]
        },
        "event_table": {
            "type": "string",
        },
        "quoted_identifiers_ignore_case": {
            "type": "boolean",
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
                external_volume=Ident(database_params.get("external_volume")) if database_params.get("external_volume") else None,
                catalog=Ident(database_params.get("catalog")) if database_params.get("catalog") else None,
                catalog_sync=Ident(database_params.get("catalog_sync")) if database_params.get("catalog_sync") else None,
                log_level=database_params.get("log_level", None),
                log_event_level=database_params.get("log_event_level", None),
                metric_level=database_params.get("metric_level", None),
                trace_level=database_params.get("trace_level", None),
                event_table=build_schema_object_ident(self.env_prefix, database_params.get("event_table"), database_name) if database_params.get("event_table") else None,
                quoted_identifiers_ignore_case=database_params.get("quoted_identifiers_ignore_case", None),
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
