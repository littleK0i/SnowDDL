from abc import abstractmethod

from snowddl.blueprint import SchemaBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class AbstractSchemaObjectResolver(AbstractResolver):
    def get_existing_objects(self):
        existing_objects = {}

        # Process schemas in parallel
        for schema_objects in self.engine.executor.map(
            self.get_existing_objects_in_schema, self.engine.schema_cache.schemas.values()
        ):
            existing_objects.update(schema_objects)

        return existing_objects

    @abstractmethod
    def get_existing_objects_in_schema(self, schema: dict):
        pass

    def destroy(self):
        # Do nothing, all schema objects are dropped automatically on DROP DATABASE or DROP SCHEMA
        pass

    def _resolve_drop(self):
        tasks = {}

        for object_full_name in sorted(self.existing_objects):
            # Object exists in blueprints, should not be dropped
            if object_full_name in self.blueprints:
                continue

            # Parent object is going to be dropped
            if self.engine.intention_cache.check_parent_drop_intention(self.object_type, object_full_name):
                continue

            schema_full_name = ".".join(object_full_name.split(".")[:2])
            schema_bp = self.config.get_blueprints_by_type(SchemaBlueprint).get(schema_full_name)

            # Object schema does not exist in blueprints, object will be dropped automatically on DROP DATABASE or DROP SCHEMA
            if schema_bp is None:
                continue

            # Objects without blueprints are allowed in sandbox schemas, should not be dropped
            if schema_bp.is_sandbox:
                continue

            tasks[object_full_name] = (self.drop_object, self.existing_objects[object_full_name])

        self._process_tasks(tasks)
