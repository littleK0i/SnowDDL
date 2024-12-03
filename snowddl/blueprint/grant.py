from typing import Union

from .ident import AbstractIdent, DatabaseIdent, SchemaIdent
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


class GrantPattern(BaseModelWithConfig):
    privilege: str
    on: ObjectType
    pattern: IdentPattern
