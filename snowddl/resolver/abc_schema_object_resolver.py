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

    def is_policy_ref_droppable(self, existing_ref: dict):
        # POLICY_REFERENCES reports references from every session, including session-scoped temporary
        # objects belonging to other sessions. Those objects are not durable, are not managed by SnowDDL,
        # and cannot be altered from here at all — the ALTER fails with "does not exist or not authorized".
        #
        # SHOW OBJECTS is session-scoped, so a temporary object of another session is simply absent from
        # the output, while a temporary object of the current session is reported with a TEMP kind.
        cur = self.engine.execute_meta(
            "SHOW OBJECTS LIKE {name:lf} IN SCHEMA {database:i}.{schema:i}",
            {
                "name": existing_ref["name"],
                "database": existing_ref["database"],
                "schema": existing_ref["schema"],
            },
        )

        for r in cur:
            if r["name"] != existing_ref["name"]:
                continue

            if "TEMP" in str(r["kind"]):
                self.engine.logger.debug(
                    f"Skipped policy reference on temporary object "
                    f"[{existing_ref['database']}.{existing_ref['schema']}.{existing_ref['name']}]"
                )

                return False

            return True

        # Not visible in this session: a temporary object of another session, or an object which was
        # dropped while its reference lingers. Warned rather than skipped silently, since the same
        # outcome would hide a real reference on an object type missing from SHOW OBJECTS output.
        self.engine.logger.warning(
            f"Skipped policy reference on object "
            f"[{existing_ref['database']}.{existing_ref['schema']}.{existing_ref['name']}], "
            f"which does not exist in the current session"
        )

        return False

    def _resolve_drop(self):
        tasks = {}

        for object_full_name in sorted(self.existing_objects):
            # Object exists in blueprints, should not be dropped
            if object_full_name in self.blueprints:
                continue

            # Another object is going to be dropped, which implicitly drops this object
            if self._check_implicit_drop_intention(object_full_name):
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
