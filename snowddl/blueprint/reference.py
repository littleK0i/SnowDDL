from abc import ABC
from typing import List, Optional

from .ident import AbstractIdent, Ident, SchemaObjectIdent
from .object_type import ObjectType
from ..model import BaseModelWithConfig


class AbstractPolicyReference(BaseModelWithConfig, ABC):
    pass


class AggregationPolicyReference(AbstractPolicyReference):
    object_type: ObjectType
    object_name: SchemaObjectIdent
    columns: List[Ident]


class AuthenticationPolicyReference(AbstractPolicyReference):
    object_type: ObjectType
    object_name: Optional[AbstractIdent] = None


class ForeignKeyReference(BaseModelWithConfig):
    columns: List[Ident]
    ref_table_name: SchemaObjectIdent
    ref_columns: List[Ident]


class IndexReference(BaseModelWithConfig):
    columns: List[Ident]
    include: Optional[List[Ident]]


class MaskingPolicyReference(AbstractPolicyReference):
    object_type: ObjectType
    object_name: SchemaObjectIdent
    columns: List[Ident]


class NetworkPolicyReference(AbstractPolicyReference):
    object_type: ObjectType
    object_name: Optional[AbstractIdent] = None


class ProjectionPolicyReference(AbstractPolicyReference):
    object_type: ObjectType
    object_name: SchemaObjectIdent
    column: Ident


class RowAccessPolicyReference(AbstractPolicyReference):
    object_type: ObjectType
    object_name: SchemaObjectIdent
    columns: List[Ident]


class TagReference(BaseModelWithConfig):
    object_type: ObjectType
    object_name: SchemaObjectIdent
    column_name: Optional[Ident]
    tag_value: str
