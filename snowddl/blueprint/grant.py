from .ident import AbstractIdent
from .object_type import ObjectType
from ..model import BaseModelWithConfig


class Grant(BaseModelWithConfig):
    privilege: str
    on: ObjectType
    name: AbstractIdent


class FutureGrant(BaseModelWithConfig):
    privilege: str
    on: ObjectType
    name: AbstractIdent
