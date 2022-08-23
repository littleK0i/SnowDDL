from setuptools import find_packages, setup
from pathlib import Path

__version__ = ""
version_path = Path(__file__).parent / 'snowddl' / 'version.py'
exec(version_path.read_text())

setup(
    name='snowddl',
    version=__version__,
    description='Object management automation tool for Snowflake',
    long_description="""
        SnowDDL is a [declarative-style](https://www.snowflake.com/blog/embracing-agile-software-delivery-and-devops-with-snowflake/) tool for object management automation in Snowflake.

        Getting started: [https://docs.snowddl.com/getting-started](https://docs.snowddl.com/getting-started)

        Main features: [https://docs.snowddl.com/features](https://docs.snowddl.com/features)

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

        Enjoy!
    """,
    long_description_content_type='text/markdown',
    url='https://github.com/littleK0i/snowddl',
    author='Vitaly Markov',
    author_email='wild.desu@gmail.com',

    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Database',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],

    keywords='snowflake database schema object change ddl sql create alter drop grant',

    packages=find_packages(),
    include_package_data = True,

    entry_points={
        'console_scripts': [
            'snowddl = snowddl.app.base:entry_point',
            'snowddl-convert = snowddl.app.convert:entry_point',
            'snowddl-singledb = snowddl.app.singledb:entry_point',
        ],
    },

    install_requires=[
        'snowflake-connector-python',
        'pyyaml',
        'jsonschema',
    ],

    extras_require={
        'test': ['pytest'],
    },

    python_requires='>=3.7',
)
