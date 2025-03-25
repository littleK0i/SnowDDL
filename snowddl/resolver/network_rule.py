from snowddl.blueprint import NetworkRuleBlueprint, SchemaObjectIdent, Ident
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class NetworkRuleResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.NETWORK_RULE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW NETWORK RULES IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "owner": r["owner"],
                "type": r["type"],
                "mode": r["mode"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(NetworkRuleBlueprint)

    def create_object(self, bp: NetworkRuleBlueprint):
        common_query = self._build_common_network_rule_sql(bp)
        create_query = self.engine.query_builder()

        create_query.append(
            "CREATE NETWORK RULE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        create_query.append(common_query)
        self.engine.execute_safe_ddl(create_query)

        return ResolveResult.CREATE

    def compare_object(self, bp: NetworkRuleBlueprint, row: dict):
        cur = self.engine.execute_meta(
            "DESC NETWORK RULE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        desc = cur.fetchone()

        if bp.type != row["type"] or bp.mode != row["mode"]:
            # Changing TYPE or MODE is only possible via full REPLACE
            self._drop_network_rule_refs(bp.full_name)

            common_query = self._build_common_network_rule_sql(bp)
            replace_query = self.engine.query_builder()

            replace_query.append(
                "CREATE OR REPLACE NETWORK RULE {full_name:i}",
                {
                    "full_name": bp.full_name,
                },
            )

            replace_query.append(common_query)
            self.engine.execute_unsafe_ddl(replace_query)

            return ResolveResult.REPLACE

        result = ResolveResult.NOCHANGE

        if ",".join(bp.value_list) != desc["value_list"]:
            if bp.value_list:
                self.engine.execute_safe_ddl(
                    "ALTER NETWORK RULE {full_name:i} SET VALUE_LIST = ({value_list})",
                    {
                        "full_name": bp.full_name,
                        "value_list": bp.value_list,
                    },
                )
            else:
                self.engine.execute_safe_ddl(
                    "ALTER NETWORK RULE {full_name:i} UNSET VALUE_LIST",
                    {
                        "full_name": bp.full_name,
                    },
                )

            result = ResolveResult.ALTER

        if bp.comment != row["comment"]:
            self.engine.execute_safe_ddl(
                "ALTER NETWORK RULE {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
            )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        network_rule_name = SchemaObjectIdent("", row["database"], row["schema"], row["name"])

        self._drop_network_rule_refs(network_rule_name)
        self._drop_network_rule(network_rule_name)

        return ResolveResult.DROP

    def _build_common_network_rule_sql(self, bp: NetworkRuleBlueprint):
        query = self.engine.query_builder()

        query.append_nl(
            "TYPE = {type}",
            {
                "type": bp.type,
            },
        )

        query.append_nl(
            "MODE = {mode}",
            {
                "mode": bp.mode,
            },
        )

        if bp.value_list:
            query.append_nl(
                "VALUE_LIST = ({value_list})",
                {
                    "value_list": bp.value_list,
                },
            )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        return query

    def _drop_network_rule(self, network_rule_name: SchemaObjectIdent):
        self.engine.execute_unsafe_ddl(
            "DROP NETWORK RULE {full_name:i}",
            {
                "full_name": network_rule_name,
            },
        )

    def _drop_network_rule_refs(self, network_rule_name: SchemaObjectIdent):
        cur = self.engine.execute_meta(
            "SELECT * FROM TABLE(snowflake.information_schema.network_rule_references(network_rule_name => {network_rule_name}))",
            {
                "network_rule_name": network_rule_name,
            },
        )

        for r in cur:
            if r["CONTAINER_TYPE"] == "NETWORK_POLICY":
                self.engine.execute_unsafe_ddl(
                    "-- Required to drop NETWORK RULE\n"
                    "ALTER NETWORK POLICY {policy_name:i} REMOVE {list_type:r} = ({network_rule_name:i})",
                    {
                        "policy_name": Ident(r["CONTAINER_NAME"]),
                        "list_type": "ALLOWED_NETWORK_RULE_LIST" if r["ACTION_TYPE"] == "ALLOW" else "BLOCKED_NETWORK_RULE_LIST",
                        "network_rule_name": network_rule_name,
                    },
                )
            elif r["CONTAINER_TYPE"] == "INTEGRATION":
                # Since INTEGRATION does not support easy removal of individual rules, we have to reset all rules completely (for now)
                self.engine.execute_unsafe_ddl(
                    "-- Required to drop NETWORK RULE\n"
                    "ALTER EXTERNAL ACCESS INTEGRATION {integration_name:i} UNSET ALLOWED_NETWORK_RULES",
                    {
                        "integration_name": Ident(r["CONTAINER_NAME"]),
                        "network_rule_name": network_rule_name,
                    },
                )
