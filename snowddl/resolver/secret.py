from snowddl.blueprint import SecretBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType


class SecretResolver(AbstractSchemaObjectResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.SECRET

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW SECRETS IN SCHEMA {database:i}.{schema:i}",
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
                "secret_type": r["secret_type"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(SecretBlueprint)

    def create_object(self, bp: SecretBlueprint):
        common_query = self._build_common_secret_sql(bp)
        create_query = self.engine.query_builder()

        create_query.append(
            "CREATE SECRET {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        create_query.append(common_query)
        self.engine.execute_safe_ddl(create_query)

        return ResolveResult.CREATE

    def compare_object(self, bp: SecretBlueprint, row: dict):
        is_replace_required = False

        # We cannot compare other parameters due to lack of data returned by SHOW and DESC commands for secrets
        if bp.type != row["secret_type"] or bp.comment != row["comment"]:
            is_replace_required = True

        if self.engine.settings.refresh_secrets:
            is_replace_required = True

        if not is_replace_required:
            return ResolveResult.NOCHANGE

        common_query = self._build_common_secret_sql(bp)
        replace_query = self.engine.query_builder()

        replace_query.append(
            "CREATE OR REPLACE SECRET {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        replace_query.append(common_query)
        self.engine.execute_safe_ddl(replace_query)

        return ResolveResult.REPLACE

    def drop_object(self, row: dict):
        self.engine.execute_safe_ddl(
            "DROP SECRET {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _build_common_secret_sql(self, bp: SecretBlueprint):
        query = self.engine.query_builder()

        query.append_nl(
            "TYPE = {type}",
            {
                "type": bp.type,
            },
        )

        if bp.api_authentication:
            query.append_nl(
                "API_AUTHENTICATION = {api_authentication:i}",
                {
                    "api_authentication": bp.api_authentication,
                },
            )

        if bp.oauth_scopes:
            query.append_nl(
                "OAUTH_SCOPES = ({oauth_scopes})",
                {
                    "oauth_scopes": bp.oauth_scopes,
                },
            )

        if bp.oauth_refresh_token:
            query.append_nl(
                "OAUTH_REFRESH_TOKEN = {oauth_refresh_token}",
                {
                    "oauth_refresh_token": bp.oauth_refresh_token,
                },
            )

        if bp.oauth_refresh_token_expiry_time:
            query.append_nl(
                "OAUTH_REFRESH_TOKEN_EXPIRY_TIME = {oauth_refresh_token_expiry_time}",
                {
                    "oauth_refresh_token_expiry_time": bp.oauth_refresh_token_expiry_time,
                },
            )

        if bp.username:
            query.append_nl(
                "USERNAME = {username}",
                {
                    "username": bp.username,
                },
            )

        if bp.password:
            query.append_nl(
                "PASSWORD = {password}",
                {
                    "password": bp.password,
                },
            )

        if bp.secret_string:
            query.append_nl(
                "SECRET_STRING = {secret_string}",
                {
                    "secret_string": bp.secret_string,
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
