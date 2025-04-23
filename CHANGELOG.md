# Changelog

## [0.49.0] - 2025-04-23

- Added initial implementation for `SEMANTIC_VIEW` object type.
- Reworked grants checking mechanism for outbound shares. Existing grants created by external tools and matching grant patterns in config will not be dropped.
- Reworked building of grant names. Now it tries to detect current env_prefix and put it into corresponding argument.
- Adjusted destroy sequence. Moved outbound share above `DATABASE` in order to mitigate shares blocking database and role drops.
- Bumped minimum Python version from 3.8 to 3.9.
- Bumped maximum Python version in tests from 3.11 to 3.12.

## [0.48.1] - 2025-04-16

- Added explicit `.rstrip(";")` call when reading `text` from `DYNAMIC_TABLE` metadata. It should help to prevent re-creation of dynamic tables.

## [0.48.0] - 2025-04-15

- Added `FILE` data type.
- Added `DATASET` object type. It is currently not managed by SnowDDL, but can be used for create and future grants in permission models.
- Added parameter `is_aggregate` for `FUNCTION` object type. It works with Python user-defined aggregate functions.

## [0.47.0] - 2025-04-09

- All parameters are now required for authentication policy. Snowflake has changed defaults recently. Hardcoding defaults is no longer a viable strategy.
- Added parameters `scheduling_mode`, `success_integration`, `log_level`, `target_completion_interval`, `serverless_task_min_statement_size`, `serverless_task_max_statement_size` for `TASK` object type.
- Added test for `TASK` with multi-statement Snowflake script.

## [0.46.0] - 2025-03-25

- Parameter `value_list` for `NETWORK_RULE` is no longer required.
- Added parameter `algorithm` for `SECRET`. Type `SYMMETRIC_KEY` is now supported.

## [0.45.0] - 2025-03-24

- Separated `DatabaseAccessRoleResolver` into `DatabaseOwnerRoleResolver`, `DatabaseReadRoleResolver`, `DatabaseWriteRoleResolver`.
- Separated `SchemaAccessRoleResolver` into `SchemaOwnerRoleResolver`, `SchemaReadRoleResolver`, `SchemaWriteRoleResolver`.
- Separated `WarehouseAccessRoleResolver` into `WarehouseMonitorRoleResolver`, `WarehouseUsageRoleResolver`.
- Moved creation of database owner roles and schema owner roles after creation of read and write roles in execution sequence order.
- Removed dependency checks from database owner roles and schema owner roles, no longer needed.
- Added `owner_schema_read`, `owner_schema_write` parameters for `DATABASE` object type. It is now possible to grant individual schema access to database owners.
- Removed permission model restrictions from `owner_database_read`, `owner_database_write` parameters of `DATABASE` object type. It is now possible to grant database access regardless of its permission model settings.

This change aims to eliminate inconsistencies related to interactions between database roles and schema roles. It should help to simplify introduction of new role types in the future.

## [0.44.4] - 2025-03-20

- Added explicit validator preventing technical roles from using `ALL` privilege. Each individual privilege must be defined explicitly.

## [0.44.3] - 2025-03-08

- Enabled `client_store_temporary_credential` for authenticator `externalbrowser`.

## [0.44.2] - 2025-03-03

- Added support for serverless alerts. Parameter `WAREHOUSE` for object type `ALERT` is now optional.
- Fixed tests for object type `USER` related to recent changes in output of `SHOW USERS` command.

## [0.44.1] - 2025-02-13

- Added workaround for `AWS_SNS_TOPIC` DIRECTORY parameter not being present in output of `DESC STAGE` command. It should be possible to use this parameter without triggering `ValueError`.

## [0.44.0] - 2025-02-12

- Reworked `OUTBOUND_SHARE` resolver. Now it supports more than 3 accounts per share. `SET ACCOUNTS` command was replaced with `ADD ACCOUNTS` and `REMOVE ACCOUNTS`, since `SET ACCOUNTS` no longer supports `SHARE_RESTRICTIONS` parameter.

## [0.43.0] - 2025-01-31

- Introduced action `validate`. It prepares and validates config, but stops right before connecting to Snowflake. It might be helpful for automated checks and git hooks.
- Removed `self.engine` from application classes. Now engine is created and closed only during `execute()` call, but not during `__init__`.

This change should not have any impact, unless you have custom application classes. In this case replace `with self.engine` call with `with self.get_engine()`. Some output functions now also accept `engine` argument instead of relying on `self.engine`.

## [0.42.1] - 2025-01-30

- Prevented SnowDDL from trying to change `OWNERSHIP` of Notebook object. This change is explicitly [not supported](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-limitations) by Snowflake.

## [0.42.0] - 2025-01-29

- Introduced logic to `.lstrip(" \n\r\t").rstrip(" \n\r\t;")` from object config parameters containing SQL snippets:
  - AGGREGATION_POLICY: `body`;
  - DYNAMIC_TABLE: `text`;
  - MASKING_POLICY: `body`;
  - MATERIALIZED_VIEW: `text`;
  - PROJECTION_POLICY: `body`;
  - ROW_ACCESS_POLICY: `body`;
  - TASK: `body`;
  - VIEW: `text`;

This change should help to prevent issues with these characters causing SnowDDL to re-create object constantly. Affected objects might be re-created once after the update.

FUNCTION and PROCEDURE are not affected by this change, since their bodies may contain code which is not SQL.

## [0.41.0] - 2025-01-26

- Changed naming for some roles automatically created by SnowDDL to prevent collisions with native Snowflake entities, specifically `DATABASE ROLES`:
  - `DatabaseRole` -> `DatabaseAccessRole`
  - `SchemaRole` -> `SchemaAccessRole`
  - `ShareRole` -> `ShareAccessRole`
  - `WarehouseRole` -> `WarehouseAccessRole`

This change affects SnowDDL internals only. Config format and business logic remains the same. Names of roles in Snowflake account remain the same. Only names of files, classes and constants were changed.

## [0.40.0] - 2025-01-08

- `VIEW` object type is now supported as a valid target for `STREAM`. Streams are resolved AFTER views.
- Added `change_tracking` parameter for views.
- Added validation of `change_tracking=True` for `EVENT_TABLE`, `TABLE` and `VIEW` targeted by `STREAM`.
- Reworked `STREAM` replace conditions. Now resolver should react to changes in `object_type` and `object_name` properly.
- Stale streams will be suggested for replacement even if all other parameters are the same. It is especially important for streams on views.
- Added "replace reasons" comments before `CREATE OR REPLACE STREAM` for better clarity. It is similar to "replace reasons" on tables.
- Renamed technical object type `EXTERNAL_VOLUME` into `VOLUME`. It is necessary for grants to operate properly.
- Added tests for streams.

## [0.39.1] - 2025-01-06

- Fixed error when `TableResolver` tries to run `DESCRIBE SEARCH OPTIMIZATION` on `TABLE` which does not exist yet.
- Fixed error when `AuthenticationPolicyResolver` tries to run `POLICY_REFERENCES()` on `USER` which does not exist yet.

These changes take effect mostly during `plan` action and should not have noticeable impact on `apply`.

## [0.39.0] - 2025-01-01

- Increased default number of workers from 8 to 32.
- Introduced basic benchmark to estimate how number of workers impacts final performance.
- Added dependency validations for DYNAMIC_TABLE, HYBRID_TABLE, TASK, VIEW.

## [0.38.0] - 2024-12-17

- Introduced initial implementation of `ICEBERG_TABLE` object type. Currently only unmanaged Iceberg tables are supported.
- Added parameters `external_volume` and `catalog` for `SCHEMA` object type, required for Iceberg tables to work.
- Split `run_test.sh` script into two scripts: `run_test_full.sh` and `run_test_lite.sh`. The Lite version does not run tests which require complicated setup for external resources. At this moment it skips Iceberg tables.
- Added `iceberg_setup.sql` for tests, helps to prepare environment for Iceberg table tests.

Managed Iceberg tables will be implemented if we see a sufficient interest from users.

## [0.37.4] - 2024-12-06

- Relaxed argument validation for `oauth_snowpark` authenticator.

## [0.37.3] - 2024-12-06

- Added `oauth_snowpark` authenticator to simplify running SnowDDL inside Snowpark containers.

## [0.37.2] - 2024-12-05

- Improved handling of new columns with default values during replace table.

## [0.37.1] - 2024-12-05

- Fixed issue with database role grants pointing to database with `schema_owner` ruleset.

## [0.37.0] - 2024-12-04

This is a major update to config parsing and validation, which introduces some breaking changes. [Read more about it](https://docs.snowddl.com/breaking-changes-log/0.37.0-december-2024).

- Moved parsing errors from `SnowDDLConfig` class into individual `Parser` classes, now works similar to `Resolvers`.
- Introduced a concept of `IdentPattern`. It is a special class used to define patterns to match object names in config.
- Introduced a concept of `GrantPattern`. It is a special class used to define grants for objects defined by `IdentPattern`.
- Significantly reworked `BusinessRoleBlueprint`, `TechnicalRoleBlueprint`, `DatabaseBlueprint`, `SchemaBlueprint`, `OutboundShareBlueprint`. Moved grant generation logic from parsers to resolvers. Programmatic config update is required.
- Introduced concept of `Validators` running after all parsers and programmatic config to validate an entire config.
- Moved some validations from existing parsers to validators.
- Improved error handling while parsing config files with multiple entities. Now each entity is processed separately and may raise a separate exception.
- Switched all calls of `information_schema.policy_references()` table function to `SNOWFLAKE` database. Other databases may not exist, especially during very first `plan` action.
- Moved database role grants for shares from `global_roles` to `share_read` parameter. Currently, there are no more uses for database role grants, so thematically it makes sense.
- Reworked `StageFileBlueprint` to operate using `Path` objects instead of strings. It helps to improve general compatibility with Windows OS.

## [0.36.2] - 2024-11-28

- Added `CORTEX_SEARCH_SERVICE` object types for grants.
- Added skip logic for virtual columns when replacing table with CTAS.

## [0.36.1] - 2024-11-25

- Attempted to fix directory separator issues inside `DirectoryScanneer` on Windows.

## [0.36.0] - 2024-11-23

- Introduced support for both `.yml` and `.yaml` config file extensions. Previously it was only `.yaml`.
- Implemented lists as possible placeholder values. Previously only scalar values were supported.
- Changed default values for `FileFormat.format_options`, `User.session_params`, `Warehouse.warehouse_params` from `None` to `{}`. It should help to prevent errors when blueprints are created dynamically in code.
- Removed `.grep()` calls and improved performance of config directory traversing.

## [0.35.1] - 2024-11-11

- Added skip for stage DIRECTORY property `DIRECTORY_NOTIFICATION_CHANNEL`. It is an informational property, should not be compared.

## [0.35.0] - 2024-11-08

- Added explicit notice when `CREATE OR REPLACE TABLE` is about to drop a column from table.
- It is now possible to set `is_sandbox: false` on schema level when `is_sandbox: true` on database level.
- Fixed ENV variable name `SNOWFLAKE_ROLE`.

## [0.34.4] - 2024-11-03

- Added missing conversion logic for `DatabaseBlueprint` when operating in SingleDB mode. It no longer prevents schemas from being dropped in this mode.

## [0.34.3] - 2024-10-18

- Added `ICEBERG_TABLE` object type to make it available for grants and permission models.

## [0.34.2] - 2024-10-18

- Added parameters `owner_database_read`, `owner_database_write` to `DATABASE` config. It only works if both current database and target database has permission model with `database_owner` ruleset.

## [0.34.1] - 2024-10-14

- Fixed issue with ACCOUNT-level policy references.

## [0.34.0] - 2024-10-13

- Introduced CLI option `--env-prefix-separator` which allows to choose separator for env prefix from one of three pre-defined variants: `__`, `_`, `$`. Default is `__`.
- Implemented `AUTHENTICATION_POLICY` object type. It can be referenced from `ACCOUNT_POLICY` and `USER` configs.
- Reworked `WAREHOUSE` resolver, implemented `resource_constraint` parameter for Snowpark-optimized warehouses.

## [0.33.0] - 2024-10-11

This is a major update to policies, which introduces some breaking changes. [Read more about it](https://docs.snowddl.com/breaking-changes-log/0.33.0-october-2024).

- Introduced `ACCOUNT_POLICY` config to set ACCOUNT-level policies. Currently only `NETWORK_POLICY` is supported, but more policy types will be added in the future.
- Reworked `NETWORK_POLICY` object type. Now it behaves similarly to other policies.
- Setting `NETWORK_POLICY` on `ACCOUNT` now requires `account_policy.yaml`. Setting it via `account_params.yaml` no longer works.
- Setting `NETWORK_POLICY` on `USER` now requires explicit `network_policy` parameter. Setting it via `session_params` no longer works.
- It is now possible (and recommended) to assign `AGGREGATION_POLICY`, `MASKING_POLICY`, `PROJECTION_POLICY`, `ROW_ACCESS_POLICY` via config of specific `TABLE` or `VIEW` instead of mentioning all references in policy config. Old `references` will keep working, but marked as "deprecated" in documentation.
- Introduced separate sequence for "destroy" action. Previously we used "apply" sequence for "destroy", but it may cause issues with some policies. Also, "destroy" sequence is much shorter overall.
- Introduced logic to remove `NETWORK_RULE` references before dropping object itself. Rule cannot be dropped if it still has references.
- `NETWORK_RULE` can now be ALTER-ed if only VALUES_LIST was changed. Previously network rules were always REPLACED.
- Added `type` parameter for `USER`.

## [0.32.0] - 2024-09-24

- Introduced basic "elapsed timers" for performance debugging. Can be enabled with `--show-timers` CLI parameter.
- Added basic support for `VECTOR` type. It can be used for `TABLE`, but not for `FUNCTION` or `PROCEDURE` due to issues with overloading.
- Converting tables with auto-increment now recognizes `ORDER` and `NOORDER` flags.
- Converting views without newline after `AS` is now possible.

## [0.31.2] - 2024-09-05

- Implemented custom `__eq__` method to check `Grants`. It helps to take into account edge case for `INTEGRATION` object grants not returning specific integration type from `SHOW GRANTS` command.

## [0.31.1] - 2024-09-05

- Fixed grants on `EXTERNAL ACCESS INTEGRATION` trying to use full object name instead of simplified object name.
- Reworked how simplified object type names are implemented internally. Now we have normal `singular` name, `singular_for_ref` used in context of policy references, `singular_for_grant` used in context of granting permissions.
- Added more specific identifier type for `ExternalAccessIntegrationBlueprint.full_name` to prevent issues with env prefix and testing.
- Fixed test for `TASK` related to Snowflake changing minimum value of `USER_TASK_MINIMUM_TRIGGER_INTERVAL_IN_SECONDS` parameter.

## [0.31.0] - 2024-08-16

- Implemented `share_read` parameter for `BUSINESS ROLE` and `owner_share_read` parameter for `DATABASE` and `SCHEMA`.
- Using `share_read` parameter now automatically generates `SHARE_ROLES` with `IMPORTED_PRIVILEGE` on specific share.
- `global_roles` parameter can now accept database roles in addition to normal roles, e.g. `SNOWFLAKE.OBJECT_VIEWER`.

## [0.30.5] - 2024-08-15

- Added missing parameters for `TASK`.
- Removed unused code and objects related to inbound `SHARES`. Such shares should be created manually by `ACCOUNTADMIN` and granted to business roles via `global_roles`.
- Skipped data metric functions when reading metadata of existing `FUNCTIONS`.

## [0.30.4] - 2024-08-05

- Added logic to actually remove blueprints from config on `remove_blueprint()` call.

## [0.30.3] - 2024-07-17

- Added `NOTEBOOK` object type, so now it can be used for grants.

## [0.30.2] - 2024-07-17

- Allowed passing raw private key with `SNOWFLAKE_PRIVATE_KEY` environment variable for convenience of GitHub actions. This is an addition to original `SNOWFLAKE_PRIVATE_KEY_PATH`, but does not require creation of file.

## [0.30.1] - 2024-07-15

- Added missing `__init__.py` to `fernet` package. Make sure this package is included by `find:` during build process.

## [0.30.0] - 2024-07-14

- Introduced built-in Fernet encryption for values in YAML configs, which is mostly useful for user passwords and various secrets.
- Added YAML tags `!encrypt` and `!decrypt`.
- Added ability to rotate keys for all config values encrypted with Fernet.
- Made `business_roles` optional for `USER` object type.

## [0.29.2] - 2024-07-11

- Fixed parsing error of `secrets` parameter for `PROCEDURE`.

## [0.29.1] - 2024-07-08

- Implemented parameters `match_by_column_name` and `include_metadata` for `PIPE` object type.
- Adjusted grant name parsing logic to extract arguments only from object types which support overloading.
- Included currently unknown data types to graceful warning logic for non-conforming identifiers. It should prevent SnowDDL from terminating with exception in case of encountering manually created `FUNCTION` or `PROCEDURE` with data type like `VECTOR` or `MAP`.

## [0.29.0] - 2024-06-12

- Implemented `AGGREGATION_POLICY`, `PROJECTION_POLICY` object types.
- Added property `exempt_other_policies` for `MASKING_POLICY`.
- Added CLI option `--apply-all-policy` to execute SQL for all types of policies.
- Prepared test objects for all types of policies.

## [0.28.3] - 2024-06-08

- Implemented graceful warning when encounter identifier which does not conform to SnowDDL standards while processing existing role grants. Previously it caused SnowDDL to stop with hard error.

## [0.28.2] - 2024-05-28

- Relaxed view parsing regexp in `VIEW` converter.

## [0.28.1] - 2024-05-21

- Refactored default permission model to init into `Config` class directly. No longer depends on parser.
- Refactored `DatabaseBlueprint` and `SchemaBlueprint` to make `permission_model` back to string and make it optional. It should help to simplify dynamic config generation scenarios when permission models do not matter.

## [0.28.0] - 2024-05-16

- Implemented more advanced pattern matching with wildcards, which is used primarily for business roles.
- Added new parameters for `DYNAMIC_TABLE` which were introduced when this object type went into General Availability.

## [0.27.2] - 2024-05-09

- Restored `USAGE` future grant on `STAGE` object type for default permission model. `READ` grant is still not enough to access external stages properly.

## [0.27.1] - 2024-05-08

- Granted schema OWNERSHIP privilege to DATABASE OWNER role. Unfortunately, it seems to be the only way to allow external tools to DROP schemas.

## [0.27.0] - 2024-05-06

This is a major update to permissions and SnowDDL internals, which introduces some breaking changes. [Read more about it](https://docs.snowddl.com/breaking-changes-log/0.27.0-may-2024).

- Introduced a concept of "Permission model", which allows to customize create grants and future grants. Previously these grants were hardcoded.
- Permission model can operate using default "schema owner" ruleset or new "database owner" ruleset, which is designed specifically for external ETL tools which try to create their own schemas, like Fivetran and Airbyte.
- Changed `OWNERSHIP` of the following object types to schema owner role: `ALERT`, `DYNAMIC_TABLE`, `EVENT_TABLE`, `STAGE`. Previously these object types were owned by SnowDDL admin role.
- Added new parameters for `SCHEMA` related to  permission management: `owner_warehouse_usage`, `owner_account_grants`, `owner_global_roles`.
- Added new parameters for `DATABASE` related to permission management: `owner_integration_usage`, `owner_warehouse_usage`, `owner_account_grants`, `owner_global_roles`.
- Added new parameters for `BUSINESS_ROLE` related to permission management: `database_owner`, `database_write`, `database_read`.
- Renamed `TECH_ROLE` to `TECHNICAL_ROLE`. Old configs with `tech_roles` parameter are still supported, no need to change anything.
- Introduced a concept of "account grants" - special type of grants on entire account. The main difference is lack of grant "name".
- Added an option to set custom `account_grants` for `TECHNICAL_ROLE`.
- Reworked internals regarding future grants. Future grants are now automatically applied to existing objects on creation. Future grants on `DATABASE` are now supported. Previously it was only supported on `SCHEMA`.
- Reworked check for exotic table types in `TABLE` resolver. Now it should no longer fail when Snowflake keeps adding and removing columns about exotic table types in `SHOW TABLES` output.
- When trying to revoke `OWNERSHIP`, it will be transferred to SnowDDL admin role instead of skipping this change altogether.
- Fixed future grants for `ALERT` object type.
- Fixed blueprint class reference for `HYBRID_TABLE`.
- Added better error messages when trying to convert `TRANSIENT` `DATABASE` or `SCHEMA` to non-`TRANSIENT`, or vice versa.

## [0.26.0] - 2024-04-16

- Introduced the concept of "intention cache". Initially it will be used to store and check intentions to drop or replace parent objects, so child objects can be properly resolved during "plan" action. For example, `DROP TABLE` command implicitly drops all table constraints, so there is no need to generate SQL commands to drop constraints.
- Reverted explicit setting to destroy schemas in SingleDB. It should be handled automatically by "intention cache" checks.
- Reworked `HYBRID_TABLE` to apply all constraints on table creation. Wait for Snowflake to resolve `FOREIGN KEY` issues with Hybrid Tables.

## [0.25.3] - 2024-04-11

- Added explicit setting to destroy schemas. Use it in SingleDB mode only. Do not attempt to destroy schemas in normal mode.
- Set `TARGET_DB` automatic placeholder earlier, but only if `--target-db` argument was specified.

## [0.25.2] - 2024-04-03

- Added CLI options `--refresh-stage-encryption` and `--refresh-secrets` to SingleDB mode.

## [0.25.1] - 2024-03-21

- Prevented SingleDB mode from asking for `--destroy-without-prefix` CLI option which is not possible to set on "destroy" action.
- Ensured schemas are correctly "destroyed" even when `DatabaseResolver` is not present in resolver sequence. Most schema objects are still being ignored.

## [0.25.0] - 2024-03-20

- Added browser-based SSO authentication (thanks to Joseph Niblo).

## [0.24.0] - 2024-03-11

- Implemented `HYBRID_TABLE` object type using short hash.
- Switched `depends_on` implementation from list to set, which should help to avoid deduplication problem entirely.
- Added SQL comment with specific replace reasons when replace table is required.
- Adjusted replace table logic to avoid unnecessary type casting when data type was not changed.
- Added some tests for `HYBRID_TABLE`.

## [0.23.2] - 2024-03-08

- Skipped all new fancy table types while working on normal `TABLE` in resolver, converter and during cloning.
- Added explicit `MONITOR`, `OPERATE` and `SELECT` privileges for `DYNAMIC_TABLE` for schema owner role.
- Added explicit `SELECT` privilege for `DYNAMIC_TABLE` for schema read role.
- Updated handling of metadata for optional arguments in `FUNCTION` and `PROCEDURE`. Snowflake replaced brackets-syntax `[, NUMBER]` with more traditional `, DEFAULT NUMBER`.

You may have to run SnowDDL with flag `--refresh-future-grants` to apply new privileges to existing dynamic tables.

## [0.23.1] - 2024-01-17

- Added `owner_integration_usage` parameter for `SCHEMA`. It grants usage privilege to schema owner role on integrations pre-configured outside SnowDDL.

## [0.23.0] - 2024-01-16

- Added remaining parameters for `TASK`.
- Added `is_ordered` for `SEQUENCE`.
- Added converter for `TASKS` (thanks to Osborne Hardison).
- Adjusted converter for `TABLE` to ignore event tables.
- Fixed issue with ALTER for `STAGE` objects trying to apply `REFRESH_ON_CREATE` to existing objects, which is not allowed.

## [0.22.1] - 2024-01-06

- Added `error_notification` for `PIPE`.
- Added tests for `PIPE`.

## [0.22.0] - 2023-11-23

- Introduced `NETWORK RULE`, `SECRET`, `EXTERNAL ACCESS INTEGRATION` object types.
- Added `EXTERNAL_ACCESS_INTEGRATIOS` and `SECRETS` parameters for functions and procedures.
- Added ability to set `default` for function and procedure arguments.
- Fixed issue with event tables being dropped while processing normal tables.
- Implemented "owner" check via `SHOW GRANTS` for `NETWORK POLICY` and `EXTERNAL ACCESS INTEGRATION`. "Owner" column is normally not available for these objects types.
- Added `--env-admin-role` CLI option.

## [0.21.0] - 2023-11-01

- Introduced custom value for application option (`SnowDDL <version>`) while opening Snowflake connection. Now it should be possible to find sessions created by SnowDDL using `SESSIONS` system view.
- Added `--query-tag` CLI option to set custom `QUERY_TAG` session parameter.
- Fixed pydantic deprecation warning related to `__fields__`.
- Added explicit `.close()` call for Snowflake connection after execution of CLI commands. It should help to terminate SnowDDL sessions earlier, regardless of `CLIENT_SESSION_KEEP_ALIVE` parameter.

## [0.20.1] - 2023-10-20

- Added additional debug logs for `VIEW` resolver in attempt to diagnose rare unnecessary re-creation problem.

## [0.20.0] - 2023-10-13

- Replaced blueprint dataclasses with `pydantic` V2 models. Dataclasses are no longer used.
- Introduced a lot of default parameter values for the majority of blueprints and related objects. It should make the custom code operating on config and blueprints more clear. It will also prevent this code from breaking when new optional parameters are added to blueprints.
- Introduced `black` for code formatting. Reformatted entire codebase.
- Introduced `ruff` for code linting. Fixed or explicitly skipped ruff warnings across the entire codebase.
- Introduced the ability to dynamically add custom blueprints and adjust existing blueprints by placing Python modules in special config directory `__custom`.
- Database names starting with `__` (double underscore) will now be ignored. It is necessary to support more special config sub-directories in future.

## [0.18.2] - 2023-08-16

- When comparing grants, run `REVOKE` commands prior to `GRANT` commands. It should help to resolve issues with `OWNERSHIP` future grant, which should be revoked before a new `OWNERSHIP` grant can be added.

## [0.18.1] - 2023-07-26

- Ignore grants for object types which are currently not supported by SnowDDL.

## [0.18.0] - 2023-07-18

- Added initial implementation of table cloning while using `--env-prefix` argument.
- Fixed issue with `STAGE` re-applying `directory` parameter on every run.
- Fixed issue with `DYNAMIC_TABLE` re-applying `target_lag` parameter on every run.
- Fixed missing `change_tracking` parameter for some `DYNAMIC_TABLE` tests.

## [0.17.1] - 2023-07-16

- Improved handling of `PRIMARY_KEY` when column list is being changed.

## [0.17.0] - 2023-07-10

- Implemented `DYNAMIC_TABLE` object type.
- Implemented `EVENT_TABLE` object type (only with `change_tracking` parameter).

## [0.16.1] - 2023-06-08

- Do not remove accounts from `OUTBOUND_SHARE` if `accounts` parameter was not set in config. Outbound shares without explicitly defined accounts are managed by Snowflake Marketplace.

## [0.16.0] - 2023-05-08

- Implemented custom YAML tag `!include`, which allows to load specific config parameters from external files. It helps to maintain proper syntax highlight for SQL snippets (such as `VIEW` text) and bodies of Java / Scala / Python UDFs.
- Added more tests for `PROCEDURE` object type.

## [0.15.0] - 2023-05-03

- Switched from packaging via legacy `setup.py` to `pyproject.toml` and `setup.cfg`.

## [0.14.4] - 2023-04-22

- Grant `CREATE FILE FORMAT` privilege for OWNER schema roles. It should help to handle common use case when external tools try to create a `FILE_FORMAT` object before running `COPY INTO` command.

## [0.14.3] - 2023-03-08

- Move `STRICT` and `IMMUTABLE` before `RUNTIME_VERSION` in SQL generated for object types `FUNCTION` and `PROCEDURE`.

## [0.14.2] - 2023-02-26

- Added `is_memoizable` for `FUNCTION` object type.
- Added tests for `FUNCTION` object type.
- Starting slash `/` in `STAGE FILE` path is now optional.
- Runtime version for `FUNCTION` and `PROCEDURE` in YAML config can now be defined either as `number` or as `string`. Previously it was only defined as string, which caused confusion for numeric versions, like Python "3.8".

## [0.14.1] - 2023-02-23

- Added `__hash__` implementation for `Ident` objects. It allows usage of such objects as keys for dictionaries.

## [0.14.0] - 2023-02-12

- Implemented `ALERT` object type.
- Added better error message for missing `text` in YAML config for `VIEW` object type.

## [0.13.0] - 2023-01-24

- Completely reworked `STAGE` object type resolver. Now it checks actual property values and does not rely on short hash anymore. `STAGE` objects will be re-created only when absolutely necessary. ALTER will be applied for the majority of changes.
- Introduced CLI option `--refresh-stage-encryption` to re-apply encryption parameters for each external `STAGE`. Normally it is not possible to compare config encryption parameters with existing parameters in Snowflake.
- Introduced a few "safe" alters for `TABLE` object type: (1) add new column, (2) change comment on table, (3) change comment on specific column. Previously all alters for `TABLE` were unsafe.
- `ROLE` resolver will no longer try to revoke `OWNERSHIP` grant on objects. This grant can only be transferred.
- `ROLE` resolver will now revoke `WRITE` permission on `STAGES` before trying to revoke `READ` permission.

## [0.12.3] - 2022-12-25

- Fixed incorrect condition checking `comment` property for `WAREHOUSE` object type, which caused every warehouse to be re-created on every run.
- `FILE_FORMAT` object type is now properly replaced when `type` was changed. Other changes are still applied using `alter file format` command.
- Added tests for `PROCEDURE` and `FILE_FORMAT` object types.

## [0.12.2] - 2022-12-04

- Fixed incorrect order of parameters when resolving `PROCEDURE` with both `comment` and `is_execute_as_caller`.
- Added protection from `FUNCTION` and `PROCEDURE` arguments with TIMESTAMP-like type and non-default precision. Snowflake bug, case 00444370.

Tests for UDFs and procedures are expected to be added in the next version.

## [0.12.1] - 2022-11-29

- Fixed a bug with `session_params` being ignored for `USER` object type. Added additional checks to tests.

## [0.12.0] - 2022-11-23

- (!breaking change!) Object types `NETWORK_POLICY` and `RESOURCE_MONITOR` now use env prefix, similar to other account-level objects. Previously env prefix was ignored for these object types.
- (!breaking change!) Object types `NETWORK_POLICY` and `RESOURCE_MONITOR` are now dropped during `destroy` action as long as `--apply-network-policy` and `--apply-resource-monitor` options are present.
- Added `global_resource_monitor` parameter for `WAREHOUSE` object type. Original `resource_monitor` now refers to monitor defined in config and managed by SnowDDL. New `global_resource_monitor` refers to monitor managed outside SnowDDL.
- User with `ACCOUNTADMIN` privileges is now required to run tests. It is not possible to test `RESOURCE_MONITOR` object type otherwise.
- Fixed a bug with `warehouse_params` not being applied for `WAREHOUSE` object type.
- Fixed a bug with `WAREHOUSE` parameters not being properly updated in specific edge cases.
- Added tests for `WAREHOUSE`, `NETWORK_POLICY`, `RESOURCE_MONITOR` object types.

## [0.11.0] - 2022-11-16

- Implement query acceleration and object parameters for `WAREHOUSE` object type.
- Prevent suggestion of individual schema object drops if an entire schema was dropped.
- Add automatic placeholder `TARGET_DB` for SingleDB mode. It holds full identifier of target database.
- Add Snowflake account name and region to context object and logs.
- Add special conversion logic for `IDENTITY` columns of object type `TABLE`. Such columns are converted into `SEQUENCE` objects automatically.
- Rework naming of tests and objects in tests. It should help to streamline and speed up implementation of new tests.
- Add complete SQL file with all commands required to set up a new Snowflake test account from scratch.

## [0.10.0] - 2022-10-19

- Add `is_transient` and `retention_time` for `TABLE` object type config.
- Add `is_transient` to `TABLE` object type converter.
- Implement advanced SEARCH OPTIMIZATION on specific columns. NB: VARIANT column paths are currently not supported due to high complexity of parsing `target` column from output of `DESC SEARCH OPTIMIZATION` command.

## [0.9.9] - 2022-10-13

- Strip trailing spaces from each line of view text during `VIEW` object type conversion. It prevents formatting issues described in [pyyaml#411 issue](https://github.com/yaml/pyyaml/issues/411).

## [0.9.8] - 2022-10-11

- Add `collate` support for `TABLE` object type conversion.

## [0.9.7] - 2022-10-05

- Try to fix markdown formatting on PyPi.
- Enable converter for object type `VIEW` (currently not documented, work in progress).

## [0.9.6] - 2022-09-09

- Prevent `USER_ROLE` resolver from dropping grants other than `ROLE` grants. User roles may accumulate random grants during normal operation from temporary tables, temporary stages, manually created objects in schemas not managed by SnowDDL.
- Change testing Snowflake account once again.

## [0.9.5] - 2022-08-29

- Implement missing `comment` parameter for `USER` object type.
- Add more tests.

## [0.9.4] - 2022-08-23

- Added new supported data type `GEOMETRY` (in addition to existing `GEOGRAPHY`).
- Added env variable `SNOWFLAKE_ENV_PREFIX` to specify `--env-prefix` without explicitly mentioning it in CLI command.
- Added a workaround for Snowflake bug, which creates a grant for hidden MATERIALIZED VIEW when search optimization is enabled for a table.
- Completely reworked an approach to tests. Now tests are executed in 3 steps, each step consists of "snowddl apply" followed by pytest execution. Now it should be much easier to add and maintain a large number of test.

## [0.9.3] - 2022-08-19

- Expose internal query builder `SnowDDLQueryBuilder` as public class. Now it can be used in external projects.
- Minor internal changes in SQL formatter.

## [0.9.2] - 2022-08-15

- Implemented proper ALTER for `FILE_FORMAT`, fixed a bug when SnowDDL tried to re-create `FILE_FORMAT` which already exists. Also, `EXTERNAL_TABLE` will not lose association with `FILE_FORMAT` after ALTER.
- Object types `EXTERNAL_FUNCTION`, `EXTERNAL_TABLE`, `FUNCTION`, `PROCEDURE` are now correctly resolved as REPLACE instead of ALTER, when object was actually replaced by `CREATE OR REPLACE ...` command.

## [0.9.1] - 2022-08-13

- Fixed incorrect encoding while opening files on Windows machines. Now it is explicitly set to `utf-8`.

## [0.9.0] - 2022-08-01

- (!breaking change!) Parameter `after` of `TASK` object type is now array of strings to support newly released [DAG-feature](https://docs.snowflake.com/en/user-guide/tasks-intro.html#dag-of-tasks). Previously it was a basic string.
- Fixed a major bug with dependency resolution, when allocated full names were not preserved between cycles properly.
- Allowed `$` (dollar sign) character in identifiers.
- Added basic `expression` parameter to `TABLE` columns, as an experimental feature. Currently, it requires fully resolved and normalized SQL expression. Otherwise, SnowDDL will fail to perform expression comparison and suggest re-creating a table on every run.
- Added `--include-databases` and `--ignore-ownership` options for `snowddl-convert` entry-point.

## [0.8.0] - 2022-07-28

- Implemented `OUTBOUND_SHARE` object type.
- Implemented test version of `INBOUND_SHARE` object type, which is currently disabled during normal execution.
- It is now possible to specify `grants` for `TECH_ROLE` and `OUTBOUND_SHARE` using [Unix-style wildcards](https://docs.python.org/3/library/fnmatch.html).
- Fixed typo in `EXTERNAL_FUNCTION` blueprint parameter `api_integration`.
- Fixed type in `TECH_ROLE` JSON-schema used to validate YAML config.
- Improved patter-matching for specific `ROLE`-types. Now it should work properly with multi-letter role-suffixes.

## [0.7.4] - 2022-07-13

- `destroy` CLI action now adds option `--apply-unsafe` automatically. Option `--destroy-without-prefix` should still provide a sufficient protection from accidentally destroying everything on production.
- Dropping object types `ROLE`, `EXTERNAL TABLE`, `STAGE` is now considered "unsafe". Dropping `ROLE` prior to dropping other objects causes re-assignment of OWNERSHIP. Dropping `EXTERNAL TABLE` causes loss of associated meta-data (e.g. files, partitions), which cannot be restored easily. Dropping `INTERNAL STAGE` destroys all files in that stage.

## [0.7.3] - 2022-07-12

- Use special exit code `8` when any errors occurred inside resolvers or converters. Previously it was returned as exit code `0`.
- If user role was dropped manually, it will now be re-created and re-granted to corresponding user automatically.

## [0.7.2] - 2022-07-01

- Fixed `default_sequence` for table columns not being converted when using `singledb` mode.
- Fixed DEFAULT value not being applied properly when adding new columns using `ALTER TABLE ... ADD COLUMN`.
- Switched to another Snowflake Trial account.

## [0.7.1] - 2022-06-29

- Ignore `TEMPORARY STAGES` created by another sessions. Such stages should not appear in `SHOW STAGES` output, but they do.

## [0.7.0] - 2022-06-27

- Added `runtime_version`, `imports`, `packages`, `handler` for `PROCEDURE` object type.
- Added ability to set multiple columns for `returns` of `PROCEDURE` object type, now it is possible to define `RETURNS TABLE (...)`.
- Added initial `collate` support for `TABLE` columns.

## [0.6.1] - 2022-06-15

- Added `packages` for `FUNCTION` object type. Now it should be possible to use fully utilize Snowpark, Python and Java UDFs.
- `SnowDDLFormatter` is now exposed as public object, if you want to use it for something other than SnowDDL.

## [0.6.0] - 2022-06-05

- Implemented first version of `snowddl-singledb` entry-point. It is a simplified version of SnowDDL to manage schemas and objects in a single database only. Account-level objects, roles and grants are NOT resolved in this mode. Please check the documentation for more details.
- Schemas will no longer produce `DROP SCHEMA ...` SQL commands during `destroy` action without `--apply-unsafe` flag, similar to schema objects. All schemas are dropped implicitly after execution of `DROP DATABASE` anyway.
- Added `database_full_name` property for `SchemaIdent` and `SchemaObjectIdent` objects to simplify access to corresponding `DatabaseIdent` object.
- Replaced `argparse.Namespace` with basic `dict` for handling of CLI arguments. It helps to streamline access to specific arguments which may not be defined in other entry-points.

## [0.5.5] - 2022-05-31

- Fix missing grants for `schema_owner`, `schema_write`, `schema_read` business role options without wildcards.

## [0.5.4] - 2022-05-31

- Speed up SnowDDL execution by loading grants and future grants of existing roles in parallel.

## [0.5.3] - 2022-05-30

- Added a basic wildcard option while setting `schema_owner`, `schema_write`, `schema_read` options for business roles to match "all schemas in database". For example: `snowddl_db.*`. At least one schema matching wildcard condition should exist in config.

It is useful for managing generic script roles when new schemas are added and / or removed frequently.

## [0.5.2] - 2022-05-30

- Identifier objects were completely reworked. Now every identifier type has its own class with every part being named.
- Simplified blueprint objects. Removed `database`, `schema`, `name` fields from schema object blueprints. All this information is available as parts of `full_name`.
- Moved complex logic for "building" identifiers into dedicated module `ident_builder`.
- Performed initial preparation and testing for "singledb" entry point, which will be added in the next version.

## [0.5.1] - 2022-05-25

- Rework internal architecture of entry-points for SnowDDL CLI interface. Now it will be much easier to add new entry-points and to partially re-use existing entry-points in your own code.

## [0.5.0] - 2022-05-24

- Added parameters `login_name`, `display_name` for `USER` object type.
- Added argument `--placeholder-values` for CLI interface. It allows passing custom placeholder values in JSON format without creation of temporary file for `--placeholder-path`.

## [0.4.10] - 2022-05-12

- Fix grants not being revoked properly for object types which do not support FUTURE GRANTs.

## [0.4.9] - 2022-05-09

- Added parameters `partition_type` and `table_format` for `EXTERNAL TABLE` object type.
- `location.file_format` is now required parameter for `EXTERNAL TABLE`.

## [0.4.8] - 2022-05-06

- `OWNERSHIP` on `STAGE` objects are no longer granted to schema OWNER role via FUTURE GRANT. All stages will be owned directly by admin role instead. Otherwise, it is not possible to use external stages without explicit grant of `USAGE` on `STORAGE_INTEGRATION` object to the current role or schema owner role, which is not desirable.

In order to fix `OWNERSHIP` on stages, you may execute the following expression for each affected schema with stages and restart SnowDDL to re-apply other grants:

```
GRANT OWNERSHIP ON ALL STAGES IN SCHEMA <database>.<schema> TO ROLE <snowddl_admin_role> REVOKE CURRENT GRANTS;
```

## [0.4.7] - 2022-05-02

- Revert to session to original `WAREHOUSE` after execution of `WarehouseResolver` if necessary. Snowflake implicitly switches to newly created `WAREHOUSE` after successful CREATE statement, which is not desirable for the rest of the session.

## [0.4.6] - 2022-04-11

- `SHOW PROCEDURES` was replaced with `SHOW USER PROCEDURES`, in line with Snowflake release notes.
- Added `owner_schema_read`, `owner_schema_write` parameters for schema. If specified, grants READ or WRITE roles from other schemas to the OWNER role of the current schema. It helps to make objects in other schemas accessible for `VIEWS` and `PROCEDURES`. Normally OWNER role can only access objects in the current schema.
- Dependency management was enabled for schema roles.

## [0.4.5] - 2022-04-02

- MD5 markers which are automatically generated for `STAGE FILES` are now uploaded directly using `file_stream` option for `.execute()` command of Snowflake Python Connector. Temporary directory is no longer used.
- `file_stream` option is now available for `.execute_safe_ddl()`, `.execute_unsafe_ddl()`. It might be used in future for more advanced operations with contents of internal stages.

## [0.4.4] - 2022-03-27

- Added technical placeholder `env_prefix` which is always available for YAML configs. It should be used to access objects in other databases when specifying `VIEW` definitions (`${{ env_prefix }}db_name.schema_name.object_name`). Objects in the same database can still be accessed without specifying database name (`schema_name.object_name`).
- Fetching list of existing `STAGE FILES` no longer fails if stage exists in blueprints, but does not exist in Snowflake account.
- Resolver for `STAGE FILES` is now skipped when "destroy" action is being called. All files are destroyed automatically when stage is deleted.

## [0.4.3] - 2022-03-17

- Replaced explicit `format_exc()` calls during config validation with modern `TracebackException.from_exception().format()` API. Pre-formatted error messages will no longer be stored in `SnowDDLConfig`, but rather be formatted on demand using `Exception` object only.
- Fixed typos in some JSON schemas.
- Simplified the way how `.resolved_objects` property is being stored for resolvers. Now it is a basic `dict` with object full name as key and `ResolveResult` enum as value.

## [0.4.2] - 2022-03-12

- Added more tests for `TABLE` and `VIEW` object types.
- Improved project description.

## [0.4.1] - 2022-03-02

- Implemented `EXTERNAL FUNCTION` object type.
- Added validation for YAML config file names for object types supporting overloading.
- Re-create "invalid" `EXTERNAL TABLES` automatically.
- Switched test account to AWS.

## [0.4.0] - 2022-02-22

- Reworked parsers. Now most exceptions raised in parsers will no longer interrupt the program, but will be stored and reported later. Each reported exception now has a proper traceback and pointer to file which most likely caused the problem.
- Implemented [placeholders](https://docs.snowddl.com/basic/yaml-placeholders) in YAML configs.
- Config path is now fully resolved prior to execution, which should help to produce consistent logs regardless of symlinks or cwd.
- Added support for `STAGE FILE` object type, which is intended mainly for packages for Snowpark functions.
- Added support for Snowpark function options: `IMPORTS`, `HANDLER`, `RUNTIME_VERSION`.

## [0.3.1] - 2022-02-18

- Use `SYSTEM$BOOTSTRAP_DATA_REQUEST` to detect edition of Snowflake account.
- Drop admin role with prefix when calling `destroy` action with `--env-prefix`. Current role of connection reverts to original role without prefix.

## [0.3.0] - 2022-02-17

- Added `NETWORK_POLICY` and `RESOURCE_MONITOR` to list of supported object types.

## [0.2.1] - 2022-02-16

- Added `is_sandbox` for `DATABASE` object type, in addition to `SCHEMA` object type.
- Dump empty `params.yaml` files for `DATABASE` and `SCHEMA` during conversion to preserve empty schemas. Empty directories cannot be pushed to Git.
- Added basic safety checks for `env_prefix`. It cannot contain double underscore `__` and it cannot end with underscore `_`.

## [0.2.0] - 2022-02-15

- Added optional `-r` (ROLE) and `-w` (WAREHOUSE) arguments for SnowDDL CLI interface.
- Added basic converters from existing `DATABASE`, `SCHEMA`, `TABLE`, `SEQUENCE` objects to SnowDDL YAML configs.
- Removed future grants from `SCHEMA ROLE (WRITE)` for `VIEW` object type.
- "Getting Started Test" workflow now runs each config version twice to detect possible changes being missed on first run.
- Fixed bug with `comment` and `default` not being applied to `TABLE` columns in some cases.
- Fixed bug with short hashes being used as byte-strings instead of properly decoded pure `ascii` representations.
- Fixed bug with other alters being applied to columns dropped from `TABLE` in some cases.
- Fixed bug with table column comment not being applied immediately on `ADD COLUMN`.
- Fixed bug with role comment not being applied immediately on `CREATE ROLE`.
- Reworked the way how `comment` is being applied to `VIEW` object type. Snowflake implicitly modifies view `text` in `SHOW VIEWS` if it contains a `comment` during `CREATE VIEW`, which breaks view checks on subsequent runs.
- If `VIEW` was replaced, the resolve result is now `REPLACE` instead of `ALTER`.

## [0.1.1] - 2022-02-11

- Fixed typing annotations for `List` and `Dict` to make it compatible with Python 3.7.

## [0.1.0] - 2022-02-10

- SnowDDL was released under an open source license.
