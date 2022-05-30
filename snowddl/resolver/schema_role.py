from snowddl.blueprint import DatabaseIdent, SchemaRoleBlueprint, SchemaBlueprint, Grant, FutureGrant, build_role_ident
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

    def get_blueprint_owner_role(self, schema_bp: SchemaBlueprint):
        grants = []
        future_grants = []

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.DATABASE,
            name=DatabaseIdent(schema_bp.full_name.env_prefix, schema_bp.full_name.database),
        ))

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.SCHEMA,
            name=schema_bp.full_name,
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
                name=schema_bp.full_name,
            ))

        ownership_object_types = [
            ObjectType.EXTERNAL_TABLE,
            ObjectType.FILE_FORMAT,
            ObjectType.FUNCTION,
            ObjectType.MATERIALIZED_VIEW,
            ObjectType.PIPE,
            ObjectType.PROCEDURE,
            ObjectType.SEQUENCE,
            ObjectType.STREAM,
            ObjectType.TABLE,
            ObjectType.TASK,
            ObjectType.VIEW,
        ]

        for object_type in ownership_object_types:
            future_grants.append(FutureGrant(
                privilege="OWNERSHIP",
                on=object_type,
                name=schema_bp.full_name,
            ))

        privileges_map = {
            ObjectType.STAGE: ['READ', 'WRITE', 'USAGE'],
        }

        for object_type, privileges in privileges_map.items():
            for privilege in privileges:
                future_grants.append(FutureGrant(
                    privilege=privilege,
                    on=object_type,
                    name=schema_bp.full_name,
                ))

        depends_on = []

        for additional_grant in schema_bp.owner_additional_grants:
            # Dependency on another schema role
            if additional_grant.on == ObjectType.ROLE and str(additional_grant.name).endswith(self.get_role_suffix()):
                depends_on.append(additional_grant.name)

            grants.append(additional_grant)

        bp = SchemaRoleBlueprint(
            full_name=build_role_ident(self.config.env_prefix, schema_bp.full_name.database, schema_bp.full_name.schema, 'OWNER', self.get_role_suffix()),
            grants=grants,
            future_grants=future_grants,
            comment=None,
            depends_on=depends_on,
        )

        return bp

    def get_blueprint_read_role(self, schema_bp: SchemaBlueprint):
        grants = []
        future_grants = []

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.DATABASE,
            name=DatabaseIdent(schema_bp.full_name.env_prefix, schema_bp.full_name.database),
        ))

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.SCHEMA,
            name=schema_bp.full_name,
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
                    name=schema_bp.full_name,
                ))

        bp = SchemaRoleBlueprint(
            full_name=build_role_ident(self.config.env_prefix, schema_bp.full_name.database, schema_bp.full_name.schema, 'READ', self.get_role_suffix()),
            grants=grants,
            future_grants=future_grants,
            comment=None,
            depends_on=[],
        )

        return bp

    def get_blueprint_write_role(self, schema_bp: SchemaBlueprint):
        grants = []
        future_grants = []

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.DATABASE,
            name=DatabaseIdent(schema_bp.full_name.env_prefix, schema_bp.full_name.database),
        ))

        grants.append(Grant(
            privilege="USAGE",
            on=ObjectType.SCHEMA,
            name=schema_bp.full_name,
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
                    name=schema_bp.full_name,
                ))

        bp = SchemaRoleBlueprint(
            full_name=build_role_ident(self.config.env_prefix, schema_bp.full_name.database, schema_bp.full_name.schema, 'WRITE', self.get_role_suffix()),
            grants=grants,
            future_grants=future_grants,
            comment=None,
            depends_on=[],
        )

        return bp
