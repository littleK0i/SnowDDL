from snowddl.blueprint import RoleBlueprint, SchemaBlueprint, Grant, FutureGrant
from snowddl.resolver.abc_role_resolver import AbstractRoleResolver, ObjectType


class SchemaRoleResolver(AbstractRoleResolver):
    def get_role_suffix(self):
        return self.config.SCHEMA_ROLE_SUFFIX

    def get_blueprints(self):
        blueprints = []

        for schema in self.config.get_blueprints_by_type(SchemaBlueprint).values():
            blueprints.append(self.get_blueprint_owner_role(schema))
            blueprints.append(self.get_blueprint_read_role(schema))
            blueprints.append(self.get_blueprint_write_role(schema))

        return {str(bp.full_name): bp for bp in blueprints}

    def get_blueprint_owner_role(self, schema: SchemaBlueprint):
        grants = []
        future_grants = []

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.DATABASE,
            name=schema.database,
        ))

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.SCHEMA,
            name=schema.full_name,
        ))

        create_object_types = [
            ObjectType.FUNCTION,
            ObjectType.PROCEDURE,
            ObjectType.TABLE,
            ObjectType.VIEW,
        ]

        for object_type in create_object_types:
            grants.append(Grant(
                privilege=f"CREATE {object_type.singular}",
                on=ObjectType.SCHEMA,
                name=schema.full_name,
            ))

        ownership_object_types = [
            ObjectType.EXTERNAL_TABLE,
            ObjectType.FILE_FORMAT,
            ObjectType.FUNCTION,
            ObjectType.MATERIALIZED_VIEW,
            ObjectType.PIPE,
            ObjectType.PROCEDURE,
            ObjectType.SEQUENCE,
            ObjectType.STAGE,
            ObjectType.STREAM,
            ObjectType.TABLE,
            ObjectType.TASK,
            ObjectType.VIEW,
        ]

        for object_type in ownership_object_types:
            future_grants.append(FutureGrant(
                privilege="OWNERSHIP",
                on=object_type,
                name=schema.full_name,
            ))

        bp = RoleBlueprint(
            full_name=self.config.build_role_ident(schema.database, schema.schema, 'OWNER', self.get_role_suffix()),
            grants=grants,
            future_grants=future_grants,
            comment=None,
        )

        return bp

    def get_blueprint_read_role(self, schema: SchemaBlueprint):
        grants = []
        future_grants = []

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.DATABASE,
            name=schema.database,
        ))

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.SCHEMA,
            name=schema.full_name,
        ))

        privileges_map = {
            ObjectType.EXTERNAL_TABLE: ['SELECT', 'REFERENCES'],
            ObjectType.FILE_FORMAT: ['USAGE'],
            ObjectType.FUNCTION: ['USAGE'],
            ObjectType.MATERIALIZED_VIEW: ['SELECT', 'REFERENCES'],
            ObjectType.PROCEDURE: ['USAGE'],
            ObjectType.STAGE: ['READ', 'USAGE'],
            ObjectType.STREAM: ['SELECT'],
            ObjectType.TABLE: ['SELECT', 'REFERENCES'],
            ObjectType.VIEW: ['SELECT', 'REFERENCES'],
        }

        for object_type, privileges in privileges_map.items():
            for privilege in privileges:
                future_grants.append(FutureGrant(
                    privilege=privilege,
                    on=object_type,
                    name=schema.full_name,
                ))

        bp = RoleBlueprint(
            full_name=self.config.build_role_ident(schema.database, schema.schema, 'READ', self.get_role_suffix()),
            grants=grants,
            future_grants=future_grants,
            comment=None,
        )

        return bp

    def get_blueprint_write_role(self, schema: SchemaBlueprint):
        grants = []
        future_grants = []

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.DATABASE,
            name=schema.database,
        ))

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.SCHEMA,
            name=schema.full_name,
        ))

        privileges_map = {
            ObjectType.STAGE: ['READ', 'WRITE'],
            ObjectType.SEQUENCE: ['USAGE'],
            ObjectType.TABLE: ['INSERT', 'UPDATE', 'DELETE', 'TRUNCATE'],
        }

        for object_type, privileges in privileges_map.items():
            for privilege in privileges:
                future_grants.append(FutureGrant(
                    privilege=privilege,
                    on=object_type,
                    name=schema.full_name,
                ))

        bp = RoleBlueprint(
            full_name=self.config.build_role_ident(schema.database, schema.schema, 'WRITE', self.get_role_suffix()),
            grants=grants,
            future_grants=future_grants,
            comment=None,
        )

        return bp
