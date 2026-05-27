"""
Unit tests for PipeResolver Snowflake-managed pipe handling.

Snowflake-managed pipes (created by the Snowpipe Streaming SDK) have is_snowflake_managed="true"
in SHOW PIPES output and cannot be dropped via DDL by any role, including ACCOUNTADMIN.
Attempting DROP PIPE on them fails with SQL error 2003.

is_snowflake_managed is not documented in the SHOW PIPES reference
(https://docs.snowflake.com/en/sql-reference/sql/show-pipes) but is present in the actual
response for Snowpipe Streaming pipes (kind=STREAMING, owner=NULL):

    {
        "is_snowflake_managed": "true",   # string, not bool
        "kind": "STREAMING",
        "owner": null,
        "definition": "COPY INTO ... FROM TABLE(DATA_SOURCE(TYPE =>'STREAMING')) ...",
        "comment": "Default pipe for Snowpipe Streaming High Performance ingestion ..."
    }
"""

from unittest.mock import MagicMock

from snowddl.resolver.pipe import PipeResolver


def make_resolver():
    engine = MagicMock()
    resolver = PipeResolver.__new__(PipeResolver)
    resolver.engine = engine
    return resolver


class TestGetExistingObjectsInSchema:
    def test_snowflake_managed_pipe_excluded(self):
        """
        Bug: get_existing_objects_in_schema does not filter out Snowflake-managed pipes,
        causing drop_object to attempt DROP PIPE and fail with SQL error 2003.
        """
        resolver = make_resolver()
        resolver.engine.execute_meta.return_value = [
            {
                "database_name": "DB1",
                "schema_name": "SC1",
                "name": "MANAGED_PIPE",
                "definition": "COPY INTO SOME_TABLE FROM TABLE(DATA_SOURCE(TYPE =>'STREAMING')) MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE",
                "integration": None,
                "pattern": None,
                "comment": "Default pipe for Snowpipe Streaming High Performance ingestion to a table. Created and managed by Snowflake.",
                "is_snowflake_managed": "true",
            }
        ]

        result = resolver.get_existing_objects_in_schema({"database": "DB1", "schema": "SC1"})

        assert "DB1.SC1.MANAGED_PIPE" not in result

