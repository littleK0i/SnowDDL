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

## Notice regarding Snowflake 6.32 (2022-10-04)

Snowflake introduced a bug in the latest version `6.32`, which changed output of `DESC TABLE` command. Length is no longer returned for data type of `VARCHAR` and `BINARY` columns with maximum length.

This change potentially breaks all schema management tools relying on output of `DESC TABLE`, including SnowDDL. It raises the following exception:

```
TypeError: int() argument must be a string, a bytes-like object or a number, not 'NoneType'
```

This problem should be fixed in `6.33` in the next few days. If you cannot wait for new release, please ask customer support to revert your Snowflake account back to `6.31`.

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

## Introduction videos

- [:video_camera: Main features](https://www.youtube.com/watch?v=e5K4jmlxvWc "SnowDDL: Main Features")
- [:video_camera: Getting started](https://www.youtube.com/watch?v=OtMebyQizRA "SnowDDL: Getting Started")

## Mini-roadmap

- ~~placeholders in YAML configs~~ (done)
- ~~documentation for dynamic config generation in Python ("advanced mode")~~ (done)
- ~~video tutorials~~ (done, but more tutorials are coming in future)
- full test coverage for all object types and transformations

## Issues? Questions? Feedback?

Please use GitHub "Issues" to report bugs and technical problems.

Please use GitHub "Discussions" to ask questions and provide feedback.

## Created by
[Vitaly Markov](https://www.linkedin.com/in/markov-vitaly/), 2022

Enjoy!
