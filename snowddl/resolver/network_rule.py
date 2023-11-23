from snowddl.blueprint import NetworkRuleBlueprint
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
        is_replace_required = False

        if (
            bp.type != row["type"]
            or bp.mode != row["mode"]
            or bp.value_list != desc["value_list"].split(",")
            or bp.comment != row["comment"]
        ):
            is_replace_required = True

        if not is_replace_required:
            return ResolveResult.NOCHANGE

        common_query = self._build_common_network_rule_sql(bp)
        replace_query = self.engine.query_builder()

        replace_query.append(
            "CREATE OR REPLACE NETWORK RULE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        replace_query.append(common_query)
        self.engine.execute_safe_ddl(replace_query)

        return ResolveResult.REPLACE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl(
            "DROP NETWORK RULE {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

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
            "VALUE_LIST = ({value_list})",
            {
                "value_list": bp.value_list,
            },
        )

        query.append_nl(
            "MODE = {mode}",
            {
                "mode": bp.mode,
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
