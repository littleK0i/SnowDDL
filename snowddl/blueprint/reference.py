from typing import List, Optional

from .ident import Ident, SchemaObjectIdent
from .object_type import ObjectType
from ..model import BaseModelWithConfig


class ForeignKeyReference(BaseModelWithConfig):
    columns: List[Ident]
    ref_table_name: SchemaObjectIdent
    ref_columns: List[Ident]


class IndexReference(BaseModelWithConfig):
    columns: List[Ident]
    include: Optional[List[Ident]]


class MaskingPolicyReference(BaseModelWithConfig):
    object_type: ObjectType
    object_name: SchemaObjectIdent
    columns: List[Ident]


class RowAccessPolicyReference(BaseModelWithConfig):
    object_type: ObjectType
    object_name: SchemaObjectIdent
    columns: List[Ident]


class TagReference(BaseModelWithConfig):
    object_type: ObjectType
    object_name: SchemaObjectIdent
    column_name: Optional[Ident]
    tag_value: str
