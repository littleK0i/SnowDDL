from typing import Union

from .ident import AbstractIdent, DatabaseIdent, SchemaIdent
from .object_type import ObjectType
from ..model import BaseModelWithConfig


class Grant(BaseModelWithConfig):
    privilege: str
    on: ObjectType
    name: AbstractIdent


class AccountGrant(BaseModelWithConfig):
    privilege: str


class FutureGrant(BaseModelWithConfig):
    privilege: str
    on_future: ObjectType
    in_parent: ObjectType
    name: Union[DatabaseIdent, SchemaIdent]
