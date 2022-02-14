# SnowDDL

[![PyPI](https://badge.fury.io/py/snowddl.svg)](https://badge.fury.io/py/snowddl)
[![Getting Started Test](https://github.com/littleK0i/SnowDDL/actions/workflows/getting_started.yml/badge.svg)](https://github.com/littleK0i/SnowDDL/actions/workflows/getting_started.yml)

SnowDDL is an advanced tool for object management automation in [Snowflake](http://snowflake.com).

It is not intended to replace other tools entirely, but to provide an alternative approach focused on practical data engineering challenges.

You may find SnowDDL useful if:

- complexity of data schema grows exponentially, and it becomes hard to manage;
- your organization has multiple Snowflake accounts for different environments (dev, stage, prod);
- your organization has multiple developers sharing the same Snowflake account;
- it is necessary to generate some objects dynamically using Python ([Data Vault](https://en.wikipedia.org/wiki/Data_vault_modeling), [Star Schema](https://en.wikipedia.org/wiki/Star_schema), etc.)

## Main features

1. SnowDDL is "stateless".
2. SnowDDL provides built-in "Role hierarchy" model.
3. SnowDDL supports ALTER TABLE ... ALTER COLUMN.
4. SnowDDL re-creates invalid views automatically.
5. SnowDDL assists your team in code review.
6. SnowDDL supports "env prefix".
7. SnowDDL strikes a good balance between dependency management overhead and parallelism.
8. SnowDDL costs very little.
9. SnowDDL configuration can be generated dynamically in Python code.

## Quick links

- [Getting started](https://docs.snowddl.com/getting-started)
- [Main features](https://docs.snowddl.com/features)
- [Object types](https://docs.snowddl.com/object-types)
- [Role hierarchy](https://docs.snowddl.com/role-hierarchy)
- [CLI interface](https://docs.snowddl.com/basic/cli)
- [YAML configs](https://docs.snowddl.com/basic/yaml-configs)
- [Changelog](/CHANGELOG.md)

## Issues? Questions? Feedback?

Please use GitHub "Issues" to report bugs and technical problems.

Please use GitHub "Discussions" to ask questions and provide feedback.

## Created by
[Vitaly Markov](https://www.linkedin.com/in/markov-vitaly/), 2022

Enjoy!
