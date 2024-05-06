from enum import Enum
from typing import List

from .object_type import ObjectType
from ..model import BaseModelWithConfig


class PermissionModelRuleset(Enum):
    DATABASE_OWNER = {
        "create_managed_access_schema": False,
        "create_database_owner_role": True,
        "create_database_write_role": True,
        "create_database_read_role": True,
        "create_schema_owner_role": False,
        "create_schema_write_role": True,
        "create_schema_read_role": True,
    }

    SCHEMA_OWNER = {
        "create_managed_access_schema": True,
        "create_database_owner_role": False,
        "create_database_write_role": False,
        "create_database_read_role": False,
        "create_schema_owner_role": True,
        "create_schema_write_role": True,
        "create_schema_read_role": True,
    }

    @property
    def create_managed_access_schema(self):
        return self.value["create_managed_access_schema"]

    @property
    def create_database_owner_role(self):
        return self.value["create_database_owner_role"]

    @property
    def create_database_write_role(self):
        return self.value["create_database_write_role"]

    @property
    def create_database_read_role(self):
        return self.value["create_database_read_role"]

    @property
    def create_schema_owner_role(self):
        return self.value["create_schema_owner_role"]

    @property
    def create_schema_write_role(self):
        return self.value["create_schema_write_role"]

    @property
    def create_schema_read_role(self):
        return self.value["create_schema_read_role"]


class PermissionModelCreateGrant(BaseModelWithConfig):
    on: ObjectType


class PermissionModelFutureGrant(BaseModelWithConfig):
    privilege: str
    on: ObjectType


class PermissionModel(BaseModelWithConfig):
    ruleset: PermissionModelRuleset = PermissionModelRuleset.SCHEMA_OWNER
    owner_create_grants: List[PermissionModelCreateGrant] = []
    owner_future_grants: List[PermissionModelFutureGrant] = []
    write_future_grants: List[PermissionModelFutureGrant] = []
    read_future_grants: List[PermissionModelFutureGrant] = []
