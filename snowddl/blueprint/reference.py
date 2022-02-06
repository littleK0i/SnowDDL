from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .ident import Ident, ComplexIdentWithPrefix
    from .object_type import ObjectType


@dataclass
class MaskingPolicyReference:
    object_type: "ObjectType"
    object_name: "ComplexIdentWithPrefix"
    columns: list["Ident"]


@dataclass
class RowAccessPolicyReference:
    object_type: "ObjectType"
    object_name: "ComplexIdentWithPrefix"
    columns: list["Ident"]


@dataclass
class TagReference:
    object_type: "ObjectType"
    object_name: "ComplexIdentWithPrefix"
    column_name: Optional["Ident"]
    tag_value: str
