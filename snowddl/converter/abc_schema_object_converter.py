from abc import ABC, abstractmethod

from snowddl.converter.abc_converter import AbstractConverter, ConvertResult, LiteralStr, FoldedStr


class AbstractSchemaObjectConverter(AbstractConverter):
    def get_existing_objects(self):
        existing_objects = {}

        # Process schemas in parallel
        for schema_objects in self.engine.executor.map(self.get_existing_objects_in_schema, self.engine.schema_cache.schemas.values()):
            existing_objects.update(schema_objects)

        return existing_objects

    @abstractmethod
    def get_existing_objects_in_schema(self, schema: dict):
        pass
