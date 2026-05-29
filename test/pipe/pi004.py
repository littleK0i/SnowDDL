import json
import os
import urllib.request

from cryptography.hazmat.primitives import serialization
from snowflake.connector.auth.keypair import AuthByKeyPair
from snowddl import SchemaIdent


def _make_jwt(account, user, private_key_pem):
    pk = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    der = pk.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    auth = AuthByKeyPair(private_key=der)
    return auth.prepare(account=account, user=user)


def _open_streaming_channel(helper):
    account    = os.environ["SNOWFLAKE_ACCOUNT"]
    env_prefix = helper.env_prefix

    database = f"{env_prefix}DB1"
    schema   = "SC1"
    pipe     = "PI004_TB1-STREAMING"
    channel  = "PI004_TEST"

    # https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-rest-api
    url  = f"https://{account}.snowflakecomputing.com/v2/streaming/databases/{database}/schemas/{schema}/pipes/{pipe}/channels/{channel}"
    data = json.dumps({"offset_token": None, "fail_on_uncommitted_rows": False}).encode()

    req = urllib.request.Request(url, data=data, method="PUT")
    jwt_token = _make_jwt(account, os.environ["SNOWFLAKE_USER"], os.environ["SNOWFLAKE_PRIVATE_KEY"])

    req.add_header("Authorization", f"Bearer {jwt_token}")
    req.add_header("X-Snowflake-Authorization-Token-Type", "KEYPAIR_JWT")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _show_managed_pipes(helper):
    cur = helper.execute(
        "SHOW PIPES IN SCHEMA {schema:i}",
        {"schema": SchemaIdent(helper.env_prefix, "db1", "sc1")},
    )
    return [r for r in cur if r.get("is_snowflake_managed") == "true"]


def test_step1(helper):
    table_show = helper.show_table("db1", "sc1", "pi004_tb1")
    assert table_show is not None

    # Open a Snowpipe Streaming channel so Snowflake auto-creates a managed pipe
    # (is_snowflake_managed=true). SnowDDL step2 will see this pipe with no
    # blueprint and must not attempt DROP PIPE on it.
    result = _open_streaming_channel(helper)
    assert result["channel_status"]["channel_status_code"] == "SUCCESS"


def test_step2(helper):
    # SnowDDL ran apply with the managed pipe present and no blueprint for it.
    # The pipe must still exist — if SnowDDL had attempted DROP PIPE it would
    # have failed with SQL error 2003 and exited non-zero before pytest ran.
    table_show = helper.show_table("db1", "sc1", "pi004_tb1")
    assert table_show is not None

    assert len(_show_managed_pipes(helper)) > 0


def test_step3(helper):
    # Table dropped — Snowflake auto-drops the managed pipe along with it.
    table_show = helper.show_table("db1", "sc1", "pi004_tb1")
    assert table_show is None

    assert len(_show_managed_pipes(helper)) == 0
