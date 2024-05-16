from typing import Optional, Union

from .data_type import DataType
from .ident import Ident, SchemaObjectIdent
from ..model import BaseModelWithConfig


class DynamicTableColumn(BaseModelWithConfig):
    name: Ident
    comment: Optional[str] = None


class ExternalTableColumn(BaseModelWithConfig):
    name: Ident
    type: DataType
    expr: str
    not_null: bool = False
    comment: Optional[str] = None


class TableColumn(BaseModelWithConfig):
    name: Ident
    type: DataType
    not_null: bool = False
    default: Optional[Union[SchemaObjectIdent, str]] = None
    expression: Optional[str] = None
    collate: Optional[str] = None
    comment: Optional[str] = None


class ViewColumn(BaseModelWithConfig):
    name: Ident
    comment: Optional[str] = None


class NameWithType(BaseModelWithConfig):
    name: Ident
    type: DataType


class ArgumentWithType(NameWithType):
    default: Optional[str] = None


class SearchOptimizationItem(BaseModelWithConfig):
    method: str
    target: Ident
