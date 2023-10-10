from typing import Optional, Union

from .data_type import DataType
from .ident import Ident, SchemaObjectIdent
from ..model import BaseModelWithConfig



class ExternalTableColumn(BaseModelWithConfig):
    name: Ident
    type: DataType
    expr: str
    not_null: bool
    comment: Optional[str]


class TableColumn(BaseModelWithConfig):
    name: Ident
    type: DataType
    not_null: bool
    default: Optional[Union[SchemaObjectIdent, str]]
    expression: Optional[str]
    collate: Optional[str]
    comment: Optional[str]


class ViewColumn(BaseModelWithConfig):
    name: Ident
    comment: Optional[str]


class NameWithType(BaseModelWithConfig):
    name: Ident
    type: DataType


class SearchOptimizationItem(BaseModelWithConfig):
    method: str
    target: Ident
