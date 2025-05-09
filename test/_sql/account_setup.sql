-- SQL script to set up a new Snowflake account for tests and GitHub workflows
-- Replace <password> placeholder statement with an actual password of your choice

-- Replace <aws_role_arn> with ARN of AWS role
-- https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration

SET PASSWORD = '<password>';
SET STORAGE_AWS_ROLE_ARN = '<storage_aws_role_arn>';

---

USE ROLE ACCOUNTADMIN;

---

CREATE ROLE SNOWDDL_ADMIN;

GRANT ROLE SYSADMIN TO ROLE SNOWDDL_ADMIN;
GRANT ROLE SECURITYADMIN TO ROLE SNOWDDL_ADMIN;

CREATE USER SNOWDDL
PASSWORD = $PASSWORD
DEFAULT_ROLE = SNOWDDL_ADMIN;

GRANT ROLE SNOWDDL_ADMIN TO USER SNOWDDL;
GRANT ROLE SNOWDDL_ADMIN TO ROLE ACCOUNTADMIN;

---

CREATE ROLE SNOWDDL_ADMIN_TEST;

GRANT ROLE ACCOUNTADMIN TO ROLE SNOWDDL_ADMIN_TEST;

CREATE USER SNOWDDL_TEST
PASSWORD = $PASSWORD
DEFAULT_ROLE = SNOWDDL_ADMIN_TEST;

GRANT ROLE SNOWDDL_ADMIN_TEST TO USER SNOWDDL_TEST;

---

CREATE WAREHOUSE SNOWDDL_WH
WAREHOUSE_SIZE = 'XSMALL'
AUTO_SUSPEND = 60
AUTO_RESUME = TRUE
INITIALLY_SUSPENDED = TRUE;

GRANT USAGE, OPERATE ON WAREHOUSE SNOWDDL_WH TO ROLE SNOWDDL_ADMIN;

ALTER USER SNOWDDL SET DEFAULT_WAREHOUSE = SNOWDDL_WH;
ALTER USER SNOWDDL_TEST SET DEFAULT_WAREHOUSE = SNOWDDL_WH;

---

GRANT CREATE SHARE, IMPORT SHARE ON ACCOUNT TO ROLE SNOWDDL_ADMIN;
GRANT OVERRIDE SHARE RESTRICTIONS ON ACCOUNT TO ROLE SNOWDDL_ADMIN;

---

CREATE STORAGE INTEGRATION TEST_STORAGE_INTEGRATION_AWS
TYPE = EXTERNAL_STAGE
STORAGE_PROVIDER = 'S3'
ENABLED = TRUE
STORAGE_AWS_ROLE_ARN = $STORAGE_AWS_ROLE_ARN
STORAGE_ALLOWED_LOCATIONS = ('*')
;

GRANT USAGE ON INTEGRATION TEST_STORAGE_INTEGRATION_AWS TO ROLE SNOWDDL_ADMIN;

---

CREATE STORAGE INTEGRATION TEST_STORAGE_INTEGRATION_GCP
TYPE = EXTERNAL_STAGE
STORAGE_PROVIDER = 'GCS'
ENABLED = TRUE
STORAGE_ALLOWED_LOCATIONS = ('*');

GRANT USAGE ON INTEGRATION TEST_STORAGE_INTEGRATION_GCP TO ROLE SNOWDDL_ADMIN;

---

CREATE API INTEGRATION TEST_API_INTEGRATION
API_PROVIDER=aws_api_gateway
API_AWS_ROLE_ARN='arn:aws:iam::123456789012:role/my_cloud_account_role'
API_ALLOWED_PREFIXES=('https://xyz.execute-api.us-west-2.amazonaws.com/production')
ENABLED=TRUE;

GRANT USAGE ON INTEGRATION TEST_API_INTEGRATION TO ROLE SNOWDDL_ADMIN;

---

CREATE SECURITY INTEGRATION TEST_API_SECURITY_INTEGRATION
TYPE = API_AUTHENTICATION
AUTH_TYPE = OAUTH2
OAUTH_CLIENT_ID = 'sz1fJgpDLRQUchFzjK0AJXg_'
OAUTH_CLIENT_SECRET = 'ks1iJKuzUMkHVEQunlhLsQUC-oEdJZdas0Py8JyE3uC4Fwah'
OAUTH_TOKEN_ENDPOINT = 'https://www.oauth.com/playground/authorization-code.html'
OAUTH_ALLOWED_SCOPES = ('photo', 'offline_access')
ENABLED = TRUE;

GRANT USAGE ON INTEGRATION TEST_API_SECURITY_INTEGRATION TO ROLE SNOWDDL_ADMIN;

---

CREATE NOTIFICATION INTEGRATION TEST_NOTIFICATION_INTEGRATION
DIRECTION = OUTBOUND
TYPE = QUEUE
NOTIFICATION_PROVIDER=AWS_SNS
AWS_SNS_ROLE_ARN='arn:aws:iam::123456789012:role/my_cloud_account_role'
AWS_SNS_TOPIC_ARN='arn:aws:sns:us-east-1:123456789012:MyTopic'
ENABLED=TRUE;

GRANT USAGE ON INTEGRATION TEST_NOTIFICATION_INTEGRATION TO ROLE SNOWDDL_ADMIN;

--- these roles have no grants, used to test global roles

CREATE ROLE TEST_GLOBAL_ROLE_1;
CREATE ROLE TEST_GLOBAL_ROLE_2;
CREATE ROLE TEST_GLOBAL_ROLE_3;
