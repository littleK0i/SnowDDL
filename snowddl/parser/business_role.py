from typing import Optional, Self

from pydantic import TypeAdapter, ConfigDict, Field, AliasChoices, model_validator, ValidationError
from pydantic.dataclasses import dataclass

from snowddl.blueprint import (
    AccountObjectIdent,
    BusinessRoleBlueprint,
    Ident,
    IdentPattern,
    build_role_ident,
    build_share_read_ident,
)
from snowddl.parser.abc_parser import AbstractParser


@dataclass(config=ConfigDict(extra='forbid', populate_by_name=True))
class BusinessRoleParams:
    database_owner: list[str] = None
    database_write: list[str] = None
    database_read: list[str] = None
    schema_owner: list[str] = None
    schema_write: list[str] = None
    schema_read: list[str] = None
    share_read: list[str] = None
    warehouse_usage: list[str] = None
    warehouse_monitor: list[str] = None
    technical_roles: list[str] = None
    _tech_roles: list[str] = Field(None, alias="tech_roles", deprecated=True, description="Deprecated in favor of technical_roles")
    global_roles: list[str] = None
    comment: str = None

    @model_validator(mode='after')
    def validate_one_of_tech_roles_properties(self) -> Self:
        if self.technical_roles and self._tech_roles:
            raise ValueError("Only one of technical_roles and tech_roles properties is allowed in Business Role")
        self.technical_roles = self.technical_roles or self._tech_roles
        self._tech_roles = None
        return self


business_role_adapter = TypeAdapter(BusinessRoleParams)
business_role_dict_adapter = TypeAdapter(dict[str, BusinessRoleParams])

business_role_json_schema = business_role_dict_adapter.json_schema()


def convert_business_role(params: dict) -> BusinessRoleParams:
    return business_role_adapter.validate_python(params)


class BusinessRoleParser(AbstractParser):
    def load_blueprints(self):
        self.parse_multi_entity_file("business_role", business_role_json_schema, self.process_business_role)

    def process_business_role(self, business_role_name, business_role_params):
        business_role = convert_business_role(business_role_params)

        # fmt: off
        bp = BusinessRoleBlueprint(
            full_name=build_role_ident(self.env_prefix, business_role_name, self.config.BUSINESS_ROLE_SUFFIX),
            database_owner=[IdentPattern(p) for p in business_role.database_owner or []],
            database_write=[IdentPattern(p) for p in business_role.database_write or []],
            database_read=[IdentPattern(p) for p in business_role.database_read or []],
            schema_owner=[IdentPattern(p) for p in business_role.schema_owner or []],
            schema_write=[IdentPattern(p) for p in business_role.schema_write or []],
            schema_read=[IdentPattern(p) for p in business_role.schema_read or []],
            share_read=[build_share_read_ident(share_name) for share_name in business_role.share_read or []],
            warehouse_usage=[AccountObjectIdent(self.env_prefix, warehouse_name) for warehouse_name in business_role.warehouse_usage or []],
            warehouse_monitor=[AccountObjectIdent(self.env_prefix, warehouse_name) for warehouse_name in business_role.warehouse_monitor or []],
            technical_roles=[
                build_role_ident(self.env_prefix, technical_role_name, self.config.TECHNICAL_ROLE_SUFFIX)
                for technical_role_name in business_role.technical_roles or []
            ],
            global_roles=[Ident(global_role_name) for global_role_name in business_role.global_roles or []],
            comment=business_role.comment,
        )
        # fmt: on

        self.config.add_blueprint(bp)

    def build_database_role_grants(self, full_database_name, grant_type):
        grants = []

        for database_bp in self.config.get_blueprints_by_type_and_pattern(DatabaseBlueprint, full_database_name).values():
            database_permission_model = self.config.get_permission_model(database_bp.permission_model)

            if database_permission_model.ruleset.create_database_owner_role:
                # Databases with "database owner" permission model are assigned directly
                grants.append(
                    Grant(
                        privilege="USAGE",
                        on=ObjectType.ROLE,
                        name=build_role_ident(
                            self.env_prefix,
                            database_bp.full_name.database,
                            grant_type,
                            self.config.DATABASE_ROLE_SUFFIX,
                        ),
                    )
                )
            elif database_permission_model.ruleset.create_schema_owner_role:
                # Databases with "schema owner" permission model are automatically expanded into individual schema roles
                grants.extend(self.build_schema_role_grants(f"{database_bp.full_name.database}.*", grant_type))

        if not grants:
            raise ValueError(f"No {ObjectType.DATABASE.plural} matched wildcard grant with pattern [{full_database_name}]")

        return grants

    def build_schema_role_grants(self, full_schema_name, grant_type):
        grants = []

        for schema_bp in self.config.get_blueprints_by_type_and_pattern(SchemaBlueprint, full_schema_name).values():
            schema_permission_model = self.config.get_permission_model(schema_bp.permission_model)

            if not schema_permission_model.ruleset.create_schema_owner_role and grant_type == self.config.OWNER_ROLE_TYPE:
                raise ValueError(
                    f"Cannot use parameter [schema_owner] for schema [{schema_bp.full_name.database}.{schema_bp.full_name.schema}] due to permission model. "
                    f"Ownership can only be granted on database level via [database_owner] parameter"
                )

            grants.append(
                Grant(
                    privilege="USAGE",
                    on=ObjectType.ROLE,
                    name=build_role_ident(
                        self.env_prefix,
                        schema_bp.full_name.database,
                        schema_bp.full_name.schema,
                        grant_type,
                        self.config.SCHEMA_ROLE_SUFFIX,
                    ),
                )
            )

        if not grants:
            raise ValueError(f"No {ObjectType.SCHEMA.plural} matched wildcard grant with pattern [{full_schema_name}]")

        return grants
