# Changelog

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
