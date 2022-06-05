from abc import abstractmethod

from snowddl.blueprint import SchemaBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class AbstractSchemaObjectResolver(AbstractResolver):
    def get_existing_objects(self):
        existing_objects = {}

        # Process schemas in parallel
        for schema_objects in self.engine.executor.map(self.get_existing_objects_in_schema, self.engine.schema_cache.schemas.values()):
            existing_objects.update(schema_objects)

        return existing_objects

    @abstractmethod
    def get_existing_objects_in_schema(self, schema: dict):
        pass

    def destroy(self):
        # Do nothing, all schema objects are dropped automatically on DROP DATABASE
        pass

    def _resolve_drop(self):
        # Drop existing objects without blueprints
        # with additional check for "sandbox" schema
        tasks = {}

        for full_name in sorted(self.existing_objects):
            if full_name not in self.blueprints and not self._is_sandbox_schema(full_name):
                tasks[full_name] = (self.drop_object, self.existing_objects[full_name])

        self._process_tasks(tasks)

    def _is_sandbox_schema(self, object_full_name):
        schema_full_name = '.'.join(object_full_name.split('.')[:2])
        schema_bp = self.config.get_blueprints_by_type(SchemaBlueprint).get(schema_full_name)

        if schema_bp and schema_bp.is_sandbox:
            return True

        return False
