from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ident import Ident
    from .object_type import ObjectType


@dataclass
class Grant:
    privilege: str
    on: "ObjectType"
    name: "Ident"


@dataclass
class FutureGrant:
    privilege: str
    on: "ObjectType"
    name: "Ident"
