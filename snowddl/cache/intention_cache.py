from collections import defaultdict
from typing import Dict, Set, TYPE_CHECKING

from snowddl.blueprint import (
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

        self.drop_intention: Dict[ObjectType, Set[str]] = defaultdict(set)
        self.replace_intention: Dict[ObjectType, Set[str]] = defaultdict(set)

        self.invalid_name_warning: Dict[ObjectType, Set[str]] = defaultdict(set)

    def add_drop_intention(self, object_type: ObjectType, object_full_name: str):
        self.drop_intention[object_type].add(object_full_name)

    def add_replace_intention(self, object_type: ObjectType, object_full_name: str):
        self.replace_intention[object_type].add(object_full_name)

    def add_invalid_name_warning(self, object_type: ObjectType, object_full_name: str):
        self.invalid_name_warning[object_type].add(object_full_name)

    def check_drop_intention(self, object_type: ObjectType, object_full_name: str):
        return object_full_name in self.drop_intention[object_type]

    def check_parent_drop_intention(self, object_type: ObjectType, object_full_name: str):
        blueprint_cls = object_type.blueprint_cls
        object_full_name_parts = object_full_name.partition("(")[0].split(".")

        database_name = ".".join(object_full_name_parts[:1])
        schema_name = ".".join(object_full_name_parts[:2])
        schema_object_name = ".".join(object_full_name_parts[:3])

        # All schemas and schema objects are implicitly dropped by DATABASE
        if issubclass(blueprint_cls, (SchemaBlueprint, SchemaObjectBlueprint)) and (
            database_name in self.drop_intention[ObjectType.DATABASE]
        ):
            return True

        # All schema objects are implicitly dropped by SCHEMA
        if issubclass(blueprint_cls, SchemaObjectBlueprint) and (schema_name in self.drop_intention[ObjectType.SCHEMA]):
            return True

        # All stage files are implicitly dropped by STAGE
        if issubclass(blueprint_cls, StageFileBlueprint) and (schema_object_name in self.drop_intention[ObjectType.STAGE]):
            return True

        # All table constraints are implicitly dropped by various TABLE types which support constraints
        if issubclass(blueprint_cls, (ForeignKeyBlueprint, PrimaryKeyBlueprint, UniqueKeyBlueprint)) and (
            schema_object_name in self.drop_intention[ObjectType.TABLE]
            or schema_object_name in self.drop_intention[ObjectType.EXTERNAL_TABLE]
            or schema_object_name in self.drop_intention[ObjectType.HYBRID_TABLE]
        ):
            return True

        return False
