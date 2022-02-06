from snowddl.blueprint import NetworkPolicyBlueprint
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class NetworkPolicyResolver(AbstractResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.NETWORK_POLICY

    def get_existing_objects(self):
        existing_objects = {}

        # LIKE is not supported for this command
        cur = self.engine.execute_meta("SHOW NETWORK POLICIES")

        for r in cur:
            existing_objects[r['name']] = {
                "name": r['name'],
                "entries_in_allowed_ip_list": r['entries_in_allowed_ip_list'],
                "entries_in_blocked_ip_list": r['entries_in_blocked_ip_list'],
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(NetworkPolicyBlueprint)

    def create_object(self, bp: NetworkPolicyBlueprint):
        query = self.engine.query_builder()

        query.append("CREATE NETWORK POLICY {name:i}", {
            "name": bp.full_name,
        })

        query.append_nl("ALLOWED_IP_LIST = ({allowed_ip_list})", {
            "allowed_ip_list": bp.allowed_ip_list,
        })

        if bp.blocked_ip_list:
            query.append_nl("BLOCKED_IP_LIST = ({blocked_ip_list})", {
                "blocked_ip_list": bp.blocked_ip_list,
            })

        self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_network_policy)

        return ResolveResult.CREATE

    def compare_object(self, bp: NetworkPolicyBlueprint, row: dict):
        cur = self.engine.execute_meta("DESC NETWORK POLICY {name:i}", {
            "name": bp.full_name,
        })

        existing_allowed_ip_list = []
        existing_blocked_ip_list = []

        for r in cur:
            if r['name'] == 'ALLOWED_IP_LIST':
                existing_allowed_ip_list = str(r['value']).split(',')
            elif r['name'] == 'BLOCKED_IP_LIST':
                existing_blocked_ip_list = str(r['value']).split(',')

        if sorted(bp.allowed_ip_list) != sorted(existing_allowed_ip_list) \
        or sorted(bp.blocked_ip_list) != sorted(existing_blocked_ip_list):
            query = self.engine.query_builder()

            query.append("ALTER NETWORK POLICY {name:i}", {
                "name": bp.full_name,
            })

            query.append_nl("ALLOWED_IP_LIST = ({allowed_ip_list})", {
                "allowed_ip_list": bp.allowed_ip_list,
            })

            if bp.blocked_ip_list:
                query.append_nl("BLOCKED_IP_LIST = ({blocked_ip_list})", {
                    "blocked_ip_list": bp.allowed_ip_list,
                })

            self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_network_policy)

            return ResolveResult.ALTER

        return ResolveResult.NOCHANGE

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl("DROP NETWORK POLICY {name:i}", {
            "name": row['name'],
        }, condition=self.engine.settings.execute_network_policy)

        return ResolveResult.DROP

    def destroy(self):
        pass
