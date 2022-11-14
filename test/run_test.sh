#!/bin/sh

# Set the following environment variables:
# - SNOWFLAKE_ACCOUNT
# - SNOWFLAKE_USER
# - SNOWFLAKE_PASSWORD
# - SNOWFLAKE_ENV_PREFIX

cd "${0%/*}"

# Cleanup
snowddl -c _config/step1 --apply-unsafe destroy

# Apply step1
snowddl -c _config/step1 --apply-unsafe apply

# Run test step1
pytest -k "step1" --tb=short */*.py

# Apply step2
snowddl -c _config/step2 --apply-unsafe --apply-replace-table apply

# Run test step2
pytest -k "step2" --tb=short */*.py

# Apply step3
snowddl -c _config/step3 --apply-unsafe --apply-replace-table apply

# Run test step3
pytest -k "step3" --tb=short */*.py
