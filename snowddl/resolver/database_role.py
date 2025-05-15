from typing import List

from snowddl.blueprint import DatabaseRoleBlueprint, Grant, GrantPattern, build_grant_name_ident
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class DatabaseRoleResolver(AbstractResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.DATABASE_ROLE

    def get_existing_objects(self):
        existing_objects = {}

        # Process schemas in parallel
        for database_objects in self.engine.executor.map(
            self.get_existing_objects_in_database, self.engine.schema_cache.databases.values()
        ):
            existing_objects.update(database_objects)

        return existing_objects

    def get_existing_objects_in_database(self, database: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW DATABASE ROLES IN DATABASE {database:i}",
            {
                "database": database["database"],
            },
        )

        for r in cur:
            full_name = f"{database['database']}.{r['name']}"
            existing_objects[full_name] = {
                "database": database["database"],
                "name": r["name"],
                "owner": r["owner"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(DatabaseRoleBlueprint)

    def create_object(self, bp: DatabaseRoleBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE DATABASE ROLE {full_name:i}",
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

        self.engine.execute_safe_ddl(query)

        for bp_grant in self.expand_grant_patterns_to_grants(bp.grant_patterns):
            self.create_grant(bp.full_name, bp_grant)

        return ResolveResult.CREATE

    def compare_object(self, bp: DatabaseRoleBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        bp_grants = self.expand_grant_patterns_to_grants(bp.grant_patterns)
        existing_grants = self.get_existing_grants(bp.full_name)

        for bp_grant in bp_grants:
            if bp_grant not in existing_grants:
                self.create_grant(bp.full_name, bp_grant)
                result = ResolveResult.GRANT

        for ex_grant in existing_grants:
            if not any(grant_pattern.is_matching_grant(ex_grant) for grant_pattern in bp.grant_patterns):
                self.drop_grant(bp.full_name, ex_grant)
                result = ResolveResult.GRANT

        if bp.comment != row["comment"]:
            self.engine.execute_safe_ddl(
                "ALTER DATABASE ROLE {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
            )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP DATABASE ROLE {database:i}.{name:i}",
            {
                "database": row["database"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def create_grant(self, role_name, grant: Grant):
        self.engine.execute_unsafe_ddl(
            "GRANT {privilege:r} ON {on:r} {name:i} TO DATABASE ROLE {role_name:i}",
            {
                "privilege": grant.privilege,
                "on": grant.on.singular,
                "name": grant.name,
                "role_name": role_name,
            },
        )

    def drop_grant(self, role_name, grant: Grant):
        self.engine.execute_unsafe_ddl(
            "REVOKE {privilege:r} ON {on:r} {name:i} FROM DATABASE ROLE {role_name:i}",
            {
                "privilege": grant.privilege,
                "on": grant.on.singular,
                "name": grant.name,
                "role_name": role_name,
            },
        )

    def get_existing_grants(self, role_name):
        grants = []

        cur = self.engine.execute_meta(
            "SHOW GRANTS TO DATABASE ROLE {role_name:i}",
            {
                "role_name": role_name,
            },
        )

        for r in cur:
            grants.append(
                Grant(
                    privilege=r["privilege"],
                    on=ObjectType[r["granted_on"]],
                    name=build_grant_name_ident(self.config.env_prefix, r["name"], ObjectType[r["granted_on"]]),
                )
            )

        return grants

    def expand_grant_patterns_to_grants(self, grant_patterns: List[GrantPattern]):
        grants = []

        for grant_pattern in grant_patterns:
            blueprints = self.config.get_blueprints_by_type_and_pattern(grant_pattern.on.blueprint_cls, grant_pattern.pattern)

            for obj_bp in blueprints.values():
                grants.append(
                    Grant(
                        privilege=grant_pattern.privilege,
                        on=grant_pattern.on,
                        name=obj_bp.full_name,
                    ),
                )

        return grants
