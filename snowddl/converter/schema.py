from snowddl.blueprint import ObjectType
from snowddl.converter.abc_converter import AbstractConverter, ConvertResult
from snowddl.parser.schema import schema_json_schema


class SchemaConverter(AbstractConverter):
    def get_object_type(self) -> ObjectType:
        return ObjectType.SCHEMA

    def get_existing_objects(self):
        return self.engine.schema_cache.schemas

    def dump_object(self, row):
        data = {}

        if row['is_transient']:
            data['is_transient'] = True

        if row['comment']:
            data['comment'] = row['comment']

        object_path = self.base_path / self._normalise_name_with_prefix(row['database']) / self._normalise_name(row['schema'])
        object_path.mkdir(mode=0o755, parents=True, exist_ok=True)

        if data:
            self._dump_file(object_path / 'params.yaml', data, schema_json_schema)
            return ConvertResult.DUMP

        return ConvertResult.EMPTY
