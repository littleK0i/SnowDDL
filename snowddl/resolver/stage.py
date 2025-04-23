from snowddl.blueprint import StageBlueprint
from snowddl.resolver.abc_schema_object_resolver import AbstractSchemaObjectResolver, ResolveResult, ObjectType
from snowddl.resolver._utils import coalesce, compare_dynamic_param_value


class StageResolver(AbstractSchemaObjectResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.STAGE

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW STAGES IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            if "TEMPORARY" in r["type"]:
                # Skip TEMPORARY stages
                continue

            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "url": r["url"] if r["url"] else None,
                "storage_integration": r["storage_integration"] if r["storage_integration"] else None,
                "owner": r["owner"],
                "type": r["type"],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(StageBlueprint)

    def create_object(self, bp: StageBlueprint):
        query = self.engine.query_builder()
        query.append(
            "CREATE STAGE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        query.append_nl(self._build_create_stage_sql(bp))
        self.engine.execute_safe_ddl(query)

        return ResolveResult.CREATE

    def compare_object(self, bp: StageBlueprint, row: dict):
        if self._is_replace_required(bp, row):
            query = self.engine.query_builder()
            query.append(
                "CREATE OR REPLACE STAGE {full_name:i}",
                {
                    "full_name": bp.full_name,
                },
            )

            query.append_nl(self._build_create_stage_sql(bp))
            self.engine.execute_unsafe_ddl(query)

            return ResolveResult.REPLACE

        # Check specific properties for potential ALTER
        existing_properties = self._get_existing_stage_properties(bp)
        result = ResolveResult.NOCHANGE

        if self._compare_url(bp, row):
            result = ResolveResult.ALTER

        if self._compare_storage_integration(bp, row):
            result = ResolveResult.ALTER

        if self._compare_directory(bp, existing_properties):
            result = ResolveResult.ALTER

        if self._compare_file_format(bp, existing_properties):
            result = ResolveResult.ALTER

        if self._compare_copy_options(bp, existing_properties):
            result = ResolveResult.ALTER

        if self._compare_comment(bp, row):
            result = ResolveResult.ALTER

        if self.engine.settings.refresh_stage_encryption and bp.url and self._refresh_encryption(bp):
            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP STAGE {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        return ResolveResult.DROP

    def _is_replace_required(self, bp: StageBlueprint, row):
        # Change of stage type from INTERNAL to EXTERNAL or vice versa
        if (bp.url and not row["url"]) or (not bp.url and row["url"]):
            return True

        if bp.url is None:
            encryption_type = coalesce(bp.encryption, {}).get("TYPE", "SNOWFLAKE_FULL").upper()

            if row["type"] == "INTERNAL" and encryption_type != "SNOWFLAKE_FULL":
                return True

            if row["type"] == "INTERNAL NO CSE" and encryption_type != "SNOWFLAKE_SSE":
                return True

        return False

    def _compare_url(self, bp: StageBlueprint, row):
        if not ((bp.url is None and row["url"] is None) or str(bp.url) == row["url"]):
            query = self.engine.query_builder()
            query.append(
                "ALTER STAGE {full_name:i} SET",
                {
                    "full_name": bp.full_name,
                },
            )

            query.append_nl(
                "URL = {url:i}",
                {
                    "url": bp.url,
                },
            )

            self.engine.execute_safe_ddl(query)

            return True

        return False

    def _compare_storage_integration(self, bp: StageBlueprint, row):
        if not (
            (bp.storage_integration is None and row["storage_integration"] is None)
            or str(bp.storage_integration) == row["storage_integration"]
        ):
            query = self.engine.query_builder()
            query.append(
                "ALTER STAGE {full_name:i} SET",
                {
                    "full_name": bp.full_name,
                },
            )

            query.append_nl(
                "STORAGE_INTEGRATION = {storage_integration:i}",
                {
                    "storage_integration": bp.storage_integration,
                },
            )

            self.engine.execute_safe_ddl(query)

            return True

        return False

    def _compare_directory(self, bp: StageBlueprint, existing_properties):
        is_alter_required = False

        # Check properties in blueprint against DESC output
        for prop_name, prop_value in coalesce(bp.directory, {}).items():
            # REFRESH_ON_CREATE is only used for CREATE command, but is not available for ALTER, must be skipped
            if prop_name == "REFRESH_ON_CREATE":
                continue

            if prop_name not in existing_properties["DIRECTORY"]:
                raise ValueError(f"Unknown DIRECTORY property [{prop_name}] for stage [{bp.full_name}]")

            if compare_dynamic_param_value(prop_value, existing_properties["DIRECTORY"][prop_name]["property_value"]):
                continue

            is_alter_required = True
            break

        # Check non-default properties in DESC output exist in blueprint
        for prop_name, prop in existing_properties["DIRECTORY"].items():
            # Informational properties, should not be compared or set explicitly
            if prop_name in ("LAST_REFRESHED_ON", "DIRECTORY_NOTIFICATION_CHANNEL"):
                continue

            if prop["property_value"] != prop["property_default"] and (prop_name not in coalesce(bp.directory, {})):
                is_alter_required = True
                break

        # If anything did not match, refresh all properties for this section
        if is_alter_required:
            query = self.engine.query_builder()
            query.append(
                "ALTER STAGE {full_name:i} SET",
                {
                    "full_name": bp.full_name,
                },
            )

            query.append_nl(self._build_directory(bp, existing_properties))
            self.engine.execute_safe_ddl(query)

        return is_alter_required

    def _compare_file_format(self, bp: StageBlueprint, existing_properties):
        # Only named FILE FORMATs are supported
        if "FORMAT_NAME" in existing_properties["STAGE_FILE_FORMAT"]:
            existing_file_format = str(existing_properties["STAGE_FILE_FORMAT"]["FORMAT_NAME"]["property_value"])
            existing_file_format = existing_file_format.replace("\\", "").replace('"', "")
        else:
            existing_file_format = None

        if not ((bp.file_format is None and existing_file_format is None) or str(bp.file_format) == existing_file_format):
            query = self.engine.query_builder()
            query.append(
                "ALTER STAGE {full_name:i} SET",
                {
                    "full_name": bp.full_name,
                },
            )

            query.append_nl(self._build_file_format(bp))
            self.engine.execute_safe_ddl(query)

            return True

        return False

    def _compare_copy_options(self, bp: StageBlueprint, existing_properties):
        is_alter_required = False

        # Check properties in blueprint against DESC output
        for prop_name, prop_value in coalesce(bp.copy_options, {}).items():
            if prop_name not in existing_properties["STAGE_COPY_OPTIONS"]:
                raise ValueError(f"Unknown COPY_OPTIONS property [{prop_name}] for stage [{bp.full_name}]")

            if compare_dynamic_param_value(prop_value, existing_properties["STAGE_COPY_OPTIONS"][prop_name]["property_value"]):
                continue

            is_alter_required = True
            break

        # Check non-default properties in DESC output exist in blueprint
        for prop_name, prop in existing_properties["STAGE_COPY_OPTIONS"].items():
            if prop["property_value"] != prop["property_default"] and (prop_name not in coalesce(bp.copy_options, {})):
                # ENFORCE_LENGTH is a mirror for TRUNCATECOLUMNS
                if prop_name == "ENFORCE_LENGTH" and "TRUNCATECOLUMNS" in coalesce(bp.copy_options, {}):
                    continue

                # TRUNCATECOLUMNS is a mirror for ENFORCE_LENGTH
                if prop_name == "TRUNCATECOLUMNS" and "ENFORCE_LENGTH" in coalesce(bp.copy_options, {}):
                    continue

                is_alter_required = True
                break

        # If anything did not match, refresh all properties for this section
        if is_alter_required:
            query = self.engine.query_builder()
            query.append(
                "ALTER STAGE {full_name:i} SET",
                {
                    "full_name": bp.full_name,
                },
            )

            query.append_nl(self._build_copy_options(bp))
            self.engine.execute_safe_ddl(query)

        return is_alter_required

    def _compare_comment(self, bp: StageBlueprint, row):
        if not ((bp.comment is None and row["comment"] is None) or str(bp.comment) == row["comment"]):
            query = self.engine.query_builder()
            query.append(
                "ALTER STAGE {full_name:i} SET",
                {
                    "full_name": bp.full_name,
                },
            )

            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

            self.engine.execute_safe_ddl(query)

            return True

        return False

    def _refresh_encryption(self, bp: StageBlueprint):
        if bp.encryption:
            query = self.engine.query_builder()
            query.append(
                "ALTER STAGE {full_name:i} SET",
                {
                    "full_name": bp.full_name,
                },
            )

            query.append_nl(self._build_encryption(bp))

            self.engine.execute_safe_ddl(query)

            return True

        return False

    def _build_directory(self, bp: StageBlueprint, existing_properties=None):
        query = self.engine.query_builder()

        if bp.directory:
            adjusted_directory = bp.directory

            # REFRESH_ON_CREATE is only used for CREATE command, but is not available for ALTER, must be skipped
            if existing_properties and "REFRESH_ON_CREATE" in adjusted_directory:
                del adjusted_directory["REFRESH_ON_CREATE"]

            if adjusted_directory:
                query.append("DIRECTORY = (")

                for k, v in adjusted_directory.items():
                    query.append(
                        "{param_name:r} = {param_value:dp}",
                        {
                            "param_name": k,
                            "param_value": v,
                        },
                    )

                query.append(")")
        else:
            query.append("DIRECTORY = ( ENABLE = FALSE )")

        return query

    def _build_file_format(self, bp: StageBlueprint):
        query = self.engine.query_builder()

        if bp.file_format:
            query.append(
                "FILE_FORMAT = ( FORMAT_NAME = {file_format:i} )",
                {
                    "file_format": bp.file_format,
                },
            )
        else:
            query.append("FILE_FORMAT = ( TYPE = CSV )")

        return query

    def _build_copy_options(self, bp: StageBlueprint):
        query = self.engine.query_builder()

        if bp.copy_options:
            query.append("COPY_OPTIONS = (")

            for k, v in bp.copy_options.items():
                query.append(
                    "{param_name:r} = {param_value:dp}",
                    {
                        "param_name": k,
                        "param_value": v,
                    },
                )

            query.append(")")
        else:
            query.append("COPY_OPTIONS = ()")

        return query

    def _build_encryption(self, bp: StageBlueprint):
        query = self.engine.query_builder()

        if bp.encryption:
            query.append("ENCRYPTION = (")

            for k, v in bp.encryption.items():
                query.append(
                    "{param_name:r} = {param_value:dp}",
                    {
                        "param_name": k,
                        "param_value": v,
                    },
                )

            query.append(")")

        # Cannot reset ENCRYPTION properties to default with ENCRYPTION = () or UNSET
        # It must be defined explicitly in config for any changes to take effect

        return query

    def _build_create_stage_sql(self, bp: StageBlueprint):
        query = self.engine.query_builder()

        if bp.url:
            query.append_nl("URL = {url}", {"url": bp.url})

        if bp.storage_integration:
            query.append_nl(
                "STORAGE_INTEGRATION = {storage_integration:i}",
                {
                    "storage_integration": bp.storage_integration,
                },
            )

        if bp.directory:
            query.append_nl(self._build_directory(bp))

        if bp.file_format:
            query.append_nl(self._build_file_format(bp))

        if bp.copy_options:
            query.append_nl(self._build_copy_options(bp))

        if bp.encryption:
            query.append_nl(self._build_encryption(bp))

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        return query

    def _get_existing_stage_properties(self, bp: StageBlueprint):
        cur = self.engine.execute_meta(
            "DESC STAGE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        result = {
            "STAGE_FILE_FORMAT": {},
            "STAGE_COPY_OPTIONS": {},
            "DIRECTORY": {},
        }

        # Add phantom parameters which should exist in output of DESC command
        # https://github.com/littleK0i/SnowDDL/issues/183
        result["DIRECTORY"]["AWS_SNS_TOPIC"] = {
            "parent_property": "DIRECTORY",
            "property": "AWS_SNS_TOPIC",
            "property_type": "String",
            "property_value": "",
            "property_default": "",
        }

        for r in cur:
            if r["parent_property"] not in result:
                result[r["parent_property"]] = {}

            result[r["parent_property"]][r["property"]] = r

        return result
