from typing import List, Optional

from .ident import Ident, SchemaObjectIdent
from ..model import BaseModelWithConfig


class SemanticViewTable(BaseModelWithConfig):
    table_alias: Optional[Ident] = None
    table_name: SchemaObjectIdent
    primary_key: Optional[List[Ident]] = None
    with_synonyms: Optional[List[str]] = None
    comment: Optional[str] = None


class SemanticViewRelationship(BaseModelWithConfig):
    relationship_identifier: Optional[Ident] = None
    table_alias: Ident
    columns: List[Ident]
    ref_table_alias: Ident
    ref_columns: List[Ident]


class SemanticViewExpression(BaseModelWithConfig):
    table_alias: Ident
    name: Ident
    sql: str
    with_synonyms: Optional[List[str]] = None
    comment: Optional[str] = None
