from snowddl.blueprint import DatabaseShareBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class InboundShareResolver(AbstractResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.DATABASE

    def get_existing_objects(self):
        existing_objects = {}

        # Inbound shares do not support env_prefix due to limitations of Snowflake
        # SHOW DATABASES without filter is not efficient, but still better than alternatives
        # Hopefully, Snowflake will provide a dedicated SHOW command for DATABASES created from INBOUND SHARES in future
        cur = self.engine.execute_meta("SHOW DATABASES")

        for r in cur:
            # Skip databases created by other roles
            if r["owner"] != self.engine.context.current_role:
                continue

            # Skip normal databases (not created from SHARES)
            if not r["origin"]:
                continue

            existing_objects[r["name"]] = {
                "database": r["name"],
                "share": r["origin"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(DatabaseShareBlueprint)

    def create_object(self, bp: DatabaseShareBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE DATABASE {full_name:i} FROM SHARE {share_name:i}",
            {
                "full_name": bp.full_name,
                "share_name": bp.share_name,
            },
        )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        self.engine.execute_safe_ddl(query, condition=self.engine.settings.execute_inbound_share)

        return ResolveResult.CREATE

    def compare_object(self, bp: DatabaseShareBlueprint, row: dict):
        query = self.engine.query_builder()

        # Database is attached to another share, re-create it
        if str(bp.share_name) != row["share"]:
            query.append(
                "CREATE OR REPLACE DATABASE {full_name:i} FROM SHARE {share_name:i}",
                {
                    "full_name": bp.full_name,
                    "share_name": bp.share_name,
                },
            )

            if bp.comment:
                query.append_nl(
                    "COMMENT = {comment}",
                    {
                        "comment": bp.comment,
                    },
                )

            self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_inbound_share)
            return ResolveResult.REPLACE

        if bp.comment != row["comment"]:
            self.engine.execute_safe_ddl(
                "ALTER DATABASE {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
                condition=self.engine.settings.execute_inbound_share,
            )

            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP DATABASE {database:i}", {"database": row["database"]}, condition=self.engine.settings.execute_inbound_share
        )

        return ResolveResult.DROP
