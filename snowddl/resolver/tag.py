from snowddl.blueprint import TagBlueprint, ObjectType, SchemaObjectIdent
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult


class TagResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.TAG

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW TAGS IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            full_name = f"{r['database_name']}.{r['schema_name']}.{r['name']}"

            existing_objects[full_name] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(TagBlueprint)

    def create_object(self, bp: TagBlueprint):
        self._create_tag(bp)
        self._apply_tag_refs(bp)

        return ResolveResult.CREATE

    def compare_object(self, bp: TagBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if self._apply_tag_refs(bp):
            result = ResolveResult.ALTER

        if row["comment"] != bp.comment:
            self.engine.execute_unsafe_ddl(
                "ALTER TAG {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
            )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self._drop_tag_refs(SchemaObjectIdent("", row["database"], row["schema"], row["name"]))
        self._drop_tag(SchemaObjectIdent("", row["database"], row["schema"], row["name"]))

        return ResolveResult.DROP

    def _create_tag(self, bp: TagBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE TAG {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        self.engine.execute_unsafe_ddl(query)

    def _drop_tag(self, tag_name: SchemaObjectIdent):
        self.engine.execute_unsafe_ddl(
            "DROP TAG {full_name:i}",
            {
                "full_name": tag_name,
            },
        )

    def _apply_tag_refs(self, bp: TagBlueprint):
        existing_tag_refs = self._get_existing_tag_refs(bp.full_name)
        applied_change = False

        for ref in bp.references:
            if ref.column_name:
                ref_key = f"{ref.object_type.name}|{ref.object_name}|{ref.column_name}|{bp.full_name}"
            else:
                ref_key = f"{ref.object_type.name}|{ref.object_name}|{bp.full_name}"

            # Tag was applied before
            if ref_key in existing_tag_refs:
                existing_tag_value = existing_tag_refs[ref_key]["tag_value"]
                del existing_tag_refs[ref_key]

                # Tag was applied with the same value
                if ref.tag_value == existing_tag_value:
                    continue

            # Apply tag
            if ref.column_name:
                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {object_name:i} MODIFY COLUMN {column_name:i} SET TAG {tag_name:i} = {tag_value}",
                    {
                        "object_type": ref.object_type.singular,
                        "object_name": ref.object_name,
                        "column_name": ref.column_name,
                        "tag_name": bp.full_name,
                    },
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {object_name:i} SET TAG {tag_name:i} = {tag_value}",
                    {
                        "object_type": ref.object_type.singular,
                        "object_name": ref.object_name,
                        "tag_name": bp.full_name,
                    },
                )

            applied_change = True

        # Remove remaining tag references which no longer exist in blueprint
        for existing_ref in existing_tag_refs.values():
            if existing_ref["column_name"]:
                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {object_name:i} MODIFY COLUMN {column_name:i} UNSET TAG {tag_name:i}",
                    {
                        "object_type": existing_ref["object_type"],
                        "database": existing_ref["database"],
                        "schema": existing_ref["schema"],
                        "name": existing_ref["name"],
                        "column_name": existing_ref["column_name"],
                        "tag_name": bp.full_name,
                    },
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {object_name:i} UNSET TAG {tag_name:i}",
                    {
                        "object_type": existing_ref["object_type"],
                        "database": existing_ref["database"],
                        "schema": existing_ref["schema"],
                        "tag_name": bp.full_name,
                    },
                )

            applied_change = True

        return applied_change

    def _drop_tag_refs(self, tag_name: SchemaObjectIdent):
        existing_policy_refs = self._get_existing_tag_refs(tag_name)

        for existing_ref in existing_policy_refs.values():
            if existing_ref["column_name"]:
                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {database:i}.{schema:i}.{name:i} MODIFY COLUMN {column_name:i} UNSET TAG {tag_name:i}",
                    {
                        "object_type": existing_ref["object_type"],
                        "database": existing_ref["database"],
                        "schema": existing_ref["schema"],
                        "name": existing_ref["name"],
                        "column_name": existing_ref["column_name"],
                        "tag_name": tag_name,
                    },
                )
            else:
                self.engine.execute_unsafe_ddl(
                    "ALTER {object_type:r} {database:i}.{schema:i}.{name:i} UNSET TAG {tag_name:i}",
                    {
                        "object_type": existing_ref["object_type"],
                        "database": existing_ref["database"],
                        "schema": existing_ref["schema"],
                        "tag_name": tag_name,
                    },
                )

    def _get_existing_tag_refs(self, tag_name: SchemaObjectIdent):
        existing_policy_refs = {}

        # TODO: discover a better way to get tag references in real time
        # Currently it is not clear how to get all tag references properly

        return existing_policy_refs
