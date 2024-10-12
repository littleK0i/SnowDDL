#!/bin/sh

# Set the following environment variables:
# - SNOWFLAKE_ACCOUNT
# - SNOWFLAKE_USER
# - SNOWFLAKE_PASSWORD
# - SNOWFLAKE_ENV_PREFIX
# - SNOWFLAKE_ENV_ADMIN_ROLE

cd "${0%/*}"

# Cleanup before
snowddl -c _config/step1 --apply-unsafe --apply-resource-monitor --apply-all-policy destroy

# Apply step1
snowddl -c _config/step1 --apply-unsafe --apply-resource-monitor --apply-all-policy apply

# Run test step1
pytest -k "step1" --tb=short */*.py

# Apply step2
`snowddl -c _config/step2 --apply-unsafe --apply-replace-table --apply-resource-monitor --apply-all-policy --refresh-stage-encryption --refresh-secrets apply`

# Run test step2
pytest -k "step2" --tb=short */*.py

# Apply step3
snowddl -c _config/step3 --apply-unsafe --apply-replace-table --apply-resource-monitor --apply-all-policy --refresh-stage-encryption --refresh-secrets apply

# Run test step3
pytest -k "step3" --tb=short */*.py

# Cleanup after
snowddl -c _config/step1 --apply-unsafe --apply-resource-monitor --apply-network-policy destroy
