from dataclasses import dataclass
from typing import Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .ident import Ident, SchemaObjectIdent
    from .data_type import DataType


@dataclass
class ExternalTableColumn:
    name: "Ident"
    type: "DataType"
    expr: str
    not_null: bool
    comment: Optional[str]


@dataclass
class TableColumn:
    name: "Ident"
    type: "DataType"
    not_null: bool
    default: Optional[Union["SchemaObjectIdent", str]]
    expression: Optional[str]
    collate: Optional[str]
    comment: Optional[str]


@dataclass
class ViewColumn:
    name: "Ident"
    comment: Optional[str]


@dataclass
class NameWithType:
    name: "Ident"
    type: "DataType"
