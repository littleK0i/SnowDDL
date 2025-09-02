from collections import defaultdict
from typing import Dict, Set, TYPE_CHECKING

from snowddl.blueprint import (
    DatabaseRoleBlueprint,
    ForeignKeyBlueprint,
    ObjectType,
    PrimaryKeyBlueprint,
    SchemaBlueprint,
    SchemaObjectBlueprint,
    StageFileBlueprint,
    UniqueKeyBlueprint,
)

if TYPE_CHECKING:
    from snowddl.engine import SnowDDLEngine


class IntentionCache:
    def __init__(self, engine: "SnowDDLEngine"):
        self.engine = engine

        self.object_drop_intention: Dict[ObjectType, Set[str]] = defaultdict(set)
        self.object_name_warning: Dict[ObjectType, Set[str]] = defaultdict(set)

        self.column_drop_intention: Dict[str, Set[str]] = defaultdict(set)

    def add_object_drop_intention(self, object_type: ObjectType, object_full_name: str):
        self.object_drop_intention[object_type].add(object_full_name)

    def add_object_name_warning(self, object_type: ObjectType, object_full_name: str):
        self.object_name_warning[object_type].add(object_full_name)

    def add_column_drop_intention(self, object_full_name: str, column_name: str):
        self.column_drop_intention[object_full_name].add(column_name)

    def check_object_drop_intention(self, object_type: ObjectType, object_full_name: str):
        return object_full_name in self.object_drop_intention[object_type]

    def check_parent_object_drop_intention(self, object_type: ObjectType, object_full_name: str):
        blueprint_cls = object_type.blueprint_cls
        object_full_name_parts = object_full_name.partition("(")[0].split(".")

        database_name = ".".join(object_full_name_parts[:1])
        schema_name = ".".join(object_full_name_parts[:2])
        schema_object_name = ".".join(object_full_name_parts[:3])

        # All schemas and schema objects are implicitly dropped by DATABASE
        if issubclass(blueprint_cls, (SchemaBlueprint, SchemaObjectBlueprint, DatabaseRoleBlueprint)) and (
            database_name in self.object_drop_intention[ObjectType.DATABASE]
        ):
            return True

        # All schema objects are implicitly dropped by SCHEMA
        if issubclass(blueprint_cls, SchemaObjectBlueprint) and (schema_name in self.object_drop_intention[ObjectType.SCHEMA]):
            return True

        # All stage files are implicitly dropped by STAGE
        if issubclass(blueprint_cls, StageFileBlueprint) and (schema_object_name in self.object_drop_intention[ObjectType.STAGE]):
            return True

        # All table constraints are implicitly dropped by various TABLE types which support constraints
        if issubclass(blueprint_cls, (ForeignKeyBlueprint, PrimaryKeyBlueprint, UniqueKeyBlueprint)) and (
            schema_object_name in self.object_drop_intention[ObjectType.TABLE]
            or schema_object_name in self.object_drop_intention[ObjectType.EXTERNAL_TABLE]
            or schema_object_name in self.object_drop_intention[ObjectType.HYBRID_TABLE]
        ):
            return True

        return False

    def check_column_drop_intention(self, object_full_name: str, column_name: str):
        return column_name in self.column_drop_intention[object_full_name]
