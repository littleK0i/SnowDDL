# SnowDDL

[![PyPI](https://badge.fury.io/py/snowddl.svg)](https://badge.fury.io/py/snowddl)
[![Getting Started](https://github.com/littleK0i/SnowDDL/actions/workflows/getting_started.yml/badge.svg)](https://github.com/littleK0i/SnowDDL/actions/workflows/getting_started.yml)
[![Pytest](https://github.com/littleK0i/SnowDDL/actions/workflows/pytest.yml/badge.svg)](https://github.com/littleK0i/SnowDDL/actions/workflows/pytest.yml)

SnowDDL is a [declarative-style](https://www.snowflake.com/blog/embracing-agile-software-delivery-and-devops-with-snowflake/) tool for object management automation in [Snowflake](http://snowflake.com).

It is not intended to replace other tools entirely, but to provide an alternative approach focused on practical data engineering challenges.

You may find SnowDDL useful if:

- complexity of object schema grows exponentially, and it becomes hard to manage;
- your organization maintains multiple Snowflake accounts (dev, stage, prod);
- your organization has multiple developers sharing the same Snowflake account and suffering from conflicts;
- it is necessary to generate some part of configuration dynamically using Python;

## Main features

1. SnowDDL is "stateless".
2. SnowDDL can revert any changes.
3. SnowDDL supports ALTER COLUMN.
4. SnowDDL provides built-in "Role hierarchy" model.
5. SnowDDL re-creates invalid views automatically.
6. SnowDDL simplifies code review.
7. SnowDDL supports creation of isolated "environments" for individual developers and CI/CD scripts.
8. SnowDDL strikes a good balance between dependency management overhead and parallelism.
9. SnowDDL configuration can be generated dynamically in Python code.
10. SnowDDL can manage packages for Java and Python UDF scripts natively.

## Quick links

- [Getting started](https://docs.snowddl.com/getting-started)
- [Main features](https://docs.snowddl.com/features)
- [Object types](https://docs.snowddl.com/object-types)
- [Role hierarchy](https://docs.snowddl.com/guides/role-hierarchy)
- [CLI interface](https://docs.snowddl.com/basic/cli)
- [YAML configs](https://docs.snowddl.com/basic/yaml-configs)
- [Changelog](/CHANGELOG.md)

## Mini-roadmap

- ~~placeholders in YAML configs~~ (done)
- full test coverage for all object types and transformations
- documentation for dynamic config generation in Python ("advanced mode")
- video tutorials

## Issues? Questions? Feedback?

Please use GitHub "Issues" to report bugs and technical problems.

Please use GitHub "Discussions" to ask questions and provide feedback.

## Created by
[Vitaly Markov](https://www.linkedin.com/in/markov-vitaly/), 2022

Enjoy!
