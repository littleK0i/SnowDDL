from abc import abstractmethod

from snowddl.blueprint import RoleBlueprint, Grant, FutureGrant, ComplexIdentWithPrefix, ComplexIdentWithPrefixAndArgs, BaseDataType
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class AbstractRoleResolver(AbstractResolver):
    @abstractmethod
    def get_role_suffix(self) -> str:
        pass

    def get_object_type(self):
        return ObjectType.ROLE

    def get_existing_objects(self):
        existing_roles = {}

        cur = self.engine.execute_meta("SHOW ROLES LIKE {pattern:lse}", {
            'pattern': (self.config.env_prefix, self.get_role_suffix()),
        })

        for r in cur:
            if r['owner'] != self.engine.context.current_role:
                continue

            existing_roles[r['name']] = {
                "role_name": r['name'],
                "grants": self.get_existing_grants(r['name']),
                "future_grants": self.get_existing_future_grants(r['name']),
                "comment": r['comment'] if r['comment'] else None,
            }

        return existing_roles

    def get_existing_grants(self, role_name):
        grants = []

        cur = self.engine.execute_meta("SHOW GRANTS TO ROLE {role_name:i}", {
            "role_name": role_name,
        })

        for r in cur:
            grants.append(Grant(
                privilege=r['privilege'],
                on=ObjectType[r['granted_on']],
                name=self.build_grant_name_ident(r['name']),
            ))

        return grants

    def get_existing_future_grants(self, role_name):
        future_grants = []

        cur = self.engine.execute_meta("SHOW FUTURE GRANTS TO ROLE {role_name:i}", {
            "role_name": role_name,
        })

        for r in cur:
            future_grants.append(FutureGrant(
                privilege=r['privilege'],
                on=ObjectType[r['grant_on']],
                name=self.build_grant_name_ident(r['name']),
            ))

        return future_grants

    def build_grant_name_ident(self, grant_name):
        parts = [p.strip('"') for p in grant_name.split('.')]
        last_part = parts[-1]

        # Remove object type component from future grant names
        if last_part.startswith('<') and last_part.endswith('>'):
            parts.pop()
        # Extract data types for arguments of functions and procedures
        elif '(' in last_part:
            start_dtypes_idx = last_part.index('(')
            finish_dtypes_idx = last_part.index(')')

            parts[-1] = last_part[0:start_dtypes_idx]

            arguments = last_part[start_dtypes_idx+1:finish_dtypes_idx]
            data_types = [BaseDataType[arg.strip(' ').split(' ')[1]] for arg in arguments.split(',')] if arguments else []

            return ComplexIdentWithPrefixAndArgs('', *parts, data_types=data_types)

        return ComplexIdentWithPrefix('', *parts)

    def create_object(self, bp: RoleBlueprint):
        query = self.engine.query_builder()

        query.append("CREATE ROLE {role_name:i}", {
            "role_name": bp.full_name,
        })

        if bp.comment:
            query.append_nl("COMMENT = {comment}", {
                "comment": bp.comment,
            })

        self.engine.execute_safe_ddl(query)

        self.engine.execute_safe_ddl("GRANT ROLE {role_name:i} TO ROLE {current_role:i}", {
            "role_name": bp.full_name,
            "current_role": self.engine.context.current_role,
        })

        for bp_grant in bp.grants:
            self.create_grant(bp.full_name, bp_grant)

        for bp_future_grant in bp.future_grants:
            self.create_future_grant(bp.full_name, bp_future_grant)

        return ResolveResult.CREATE

    def compare_object(self, bp: RoleBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        if bp.comment != row['comment']:
            self.engine.execute_safe_ddl("ALTER ROLE {role_name:i} SET COMMENT = {comment}", {
                "role_name": bp.full_name,
                "comment": bp.comment,
            })

            result = ResolveResult.ALTER

        for bp_grant in bp.grants:
            if bp_grant not in row['grants']:
                self.create_grant(bp.full_name, bp_grant)
                result = ResolveResult.GRANT

        for existing_grant in row['grants']:
            if existing_grant not in bp.grants \
            and existing_grant.on.is_future_grant_supported \
            and self.grant_to_future_grant(existing_grant) not in bp.future_grants:
                self.drop_grant(bp.full_name, existing_grant)
                result = ResolveResult.GRANT

        for bp_future_grant in bp.future_grants:
            if bp_future_grant not in row['future_grants']:
                self.create_future_grant(bp.full_name, bp_future_grant)
                result = ResolveResult.GRANT

            if self.engine.settings.refresh_future_grants:
                self.refresh_future_grant(bp.full_name, bp_future_grant)
                result = ResolveResult.GRANT

        for existing_future_grant in row['future_grants']:
            if existing_future_grant not in bp.future_grants:
                self.drop_future_grant(bp.full_name, existing_future_grant)
                result = ResolveResult.GRANT

        return result

    def drop_object(self, row: dict):
        # All grants and future grants are destroyed automatically
        self.engine.execute_safe_ddl("DROP ROLE {role_name:i}", {
            "role_name": row['role_name'],
        })

        return ResolveResult.DROP

    def create_grant(self, role_name, grant: Grant):
        if grant.privilege == "USAGE" and grant.on == ObjectType.ROLE:
            self.engine.execute_safe_ddl("GRANT ROLE {name:i} TO ROLE {role_name:i}", {
                "name": grant.name,
                "role_name": role_name,
            })
        else:
            self.engine.execute_safe_ddl("GRANT {privilege:r} ON {on:r} {name:i} TO ROLE {role_name:i}", {
                "privilege": grant.privilege,
                "on": grant.on.singular,
                "name": grant.name,
                "role_name": role_name,
            })

    def drop_grant(self, role_name, grant: Grant):
        if grant.privilege == "USAGE" and grant.on == ObjectType.ROLE:
            self.engine.execute_safe_ddl("REVOKE ROLE {name:i} FROM ROLE {role_name:i}", {
                "name": grant.name,
                "role_name": role_name,
            })
        else:
            self.engine.execute_safe_ddl("REVOKE {privilege:r} ON {on:r} {name:i} FROM ROLE {role_name:i}", {
                "privilege": grant.privilege,
                "on": grant.on.singular,
                "name": grant.name,
                "role_name": role_name,
            })

    def create_future_grant(self, role_name, grant: FutureGrant):
        self.engine.execute_safe_ddl("GRANT {privilege:r} ON FUTURE {on_plural:r} IN SCHEMA {name:i} TO ROLE {role_name:i}", {
            "privilege": grant.privilege,
            "on_plural": grant.on.plural,
            "name": grant.name,
            "role_name": role_name,
        })

    def drop_future_grant(self, role_name, grant: FutureGrant):
        self.engine.execute_safe_ddl("REVOKE {privilege:r} ON FUTURE {on_plural:r} IN SCHEMA {name:i} FROM ROLE {role_name:i}", {
            "privilege": grant.privilege,
            "on_plural": grant.on.plural,
            "name": grant.name,
            "role_name": role_name,
        })

    def refresh_future_grant(self, role_name, grant: FutureGrant):
        # Bulk grant on objects of type PIPE to ROLE is restricted (by Snowflake)
        if grant.on == ObjectType.PIPE:
            return

        self.engine.execute_safe_ddl("GRANT {privilege:r} ON ALL {on_plural:r} IN SCHEMA {name:i} TO ROLE {role_name:i}", {
            "privilege": grant.privilege,
            "on_plural": grant.on.plural,
            "name": grant.name,
            "role_name": role_name,
        })

    def grant_to_future_grant(self, grant: Grant):
        future_grant = FutureGrant(
            privilege=grant.privilege,
            on=grant.on,
            name=ComplexIdentWithPrefix(grant.name.env_prefix, *grant.name.parts[:-1]) if isinstance(grant.name, ComplexIdentWithPrefix) else grant.name
        )

        return future_grant
