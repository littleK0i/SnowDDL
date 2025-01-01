#!/bin/sh

# Set the following environment variables:
# - SNOWFLAKE_ACCOUNT
# - SNOWFLAKE_USER
# - SNOWFLAKE_PASSWORD
# - SNOWFLAKE_ENV_PREFIX
# - SNOWFLAKE_ENV_ADMIN_ROLE

cd "${0%/*}"

# Cleanup before
snowddl -c _config/perf_step1 --apply-unsafe destroy

# Apply step1
snowddl -c _config/perf_step1 --apply-unsafe --show-timers apply

# Apply step2
snowddl -c _config/perf_step2 --apply-unsafe --show-timers apply

# Apply step3
snowddl -c _config/perf_step3 --apply-unsafe --show-timers apply

# Cleanup after
snowddl -c _config/perf_step1 --apply-unsafe destroy
