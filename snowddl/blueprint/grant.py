from typing import Union

from .ident import AbstractIdent, AbstractIdentWithPrefix, DatabaseIdent, SchemaIdent, SchemaObjectIdent
from .ident_pattern import IdentPattern
from .object_type import ObjectType
from ..model import BaseModelWithConfig


class Grant(BaseModelWithConfig):
    privilege: str
    on: ObjectType
    name: AbstractIdent

    def __eq__(self, other):
        if not isinstance(other, Grant):
            raise NotImplementedError

        if self.privilege != other.privilege:
            return False

        if self.on.singular_for_grant != other.on.singular_for_grant:
            return False

        if self.name != other.name:
            return False

        return True


class AccountGrant(BaseModelWithConfig):
    privilege: str


class FutureGrant(BaseModelWithConfig):
    privilege: str
    on_future: ObjectType
    in_parent: ObjectType
    name: Union[DatabaseIdent, SchemaIdent]

    def is_matching_grant(self, grant: Grant):
        if not grant.on.is_future_grant_supported:
            return False

        if self.privilege != grant.privilege:
            return False

        if self.on_future.singular_for_grant != grant.on.singular_for_grant:
            return False

        if self.in_parent == ObjectType.DATABASE:
            if not isinstance(grant.name, (SchemaIdent, SchemaObjectIdent)):
                return False

            if self.name != grant.name.database_full_name:
                return False

        if self.in_parent == ObjectType.SCHEMA:
            if not isinstance(grant.name, SchemaObjectIdent):
                return False

            if self.name != grant.name.schema_full_name:
                return False

        return True


class GrantPattern(BaseModelWithConfig):
    privilege: str
    on: ObjectType
    pattern: IdentPattern

    def is_matching_grant(self, grant: Grant):
        if self.privilege != grant.privilege:
            return False

        if self.on.singular_for_grant != grant.on.singular_for_grant:
            return False

        if not isinstance(grant.name, AbstractIdentWithPrefix):
            return False

        if not self.pattern.is_match_ident(grant.name):
            return False

        return True


class FutureGrantPattern(BaseModelWithConfig):
    privilege: str
    on_future: ObjectType
    in_parent: ObjectType
    pattern: IdentPattern
