import pytest
from pydantic import ValidationError

from snowddl.parser.business_role import business_role_json_schema, convert_business_role, BusinessRoleParams


def test_json_schema():
    expected_json_schema = {
        '$defs': {
            'BusinessRoleParams': {
                'additionalProperties': False,
                'properties': {
                    'comment': {
                        'default': None,
                        'title': 'Comment',
                        'type': 'string'
                    },
                    'database_owner': {
                        'default': None,
                        'items': {'type': 'string'},
                        'title': 'Database Owner',
                        'type': 'array'
                    },
                    'database_read': {
                        'default': None,
                        'items': {'type': 'string'},
                        'title': 'Database Read',
                        'type': 'array'
                    },
                    'database_write': {
                        'default': None,
                        'items': {'type': 'string'},
                        'title': 'Database Write',
                        'type': 'array'
                    },
                    'global_roles': {
                        'default': None,
                        'items': {'type': 'string'},
                        'title': 'Global Roles',
                        'type': 'array'
                    },
                    'schema_owner': {
                        'default': None,
                        'items': {'type': 'string'},
                        'title': 'Schema Owner',
                        'type': 'array'
                    },
                    'schema_read': {
                        'default': None,
                        'items': {'type': 'string'},
                        'title': 'Schema Read',
                        'type': 'array'
                    },
                    'schema_write': {
                        'default': None,
                        'items': {'type': 'string'},
                        'title': 'Schema Write',
                        'type': 'array'
                    },
                    'share_read': {
                        'default': None,
                        'items': {'type': 'string'},
                        'title': 'Share Read',
                        'type': 'array'
                    },
                    'tech_roles': {
                        'default': None,
                        'items': {'type': 'string'},
                        'deprecated': True,
                        'description': 'Deprecated in favor of technical_roles',
                        'title': 'Tech Roles',
                        'type': 'array'
                    },
                    'technical_roles': {
                        'default': None,
                        'items': {'type': 'string'},
                        'title': 'Technical Roles',
                        'type': 'array'
                    },
                    'warehouse_monitor': {
                        'default': None,
                        'items': {'type': 'string'},
                        'title': 'Warehouse Monitor',
                        'type': 'array'
                    },
                    'warehouse_usage': {
                        'default': None,
                        'items': {'type': 'string'},
                        'title': 'Warehouse Usage',
                        'type': 'array'
                    }
                },
                'title': 'BusinessRoleParams',
                'type': 'object'
            }
        },
        'additionalProperties': {'$ref': '#/$defs/BusinessRoleParams'},
        'type': 'object'
    }
    assert expected_json_schema == business_role_json_schema


def test_convert_business_role_empty():
    assert BusinessRoleParams() == convert_business_role({})


def test_convert_business_role_simple():
    assert BusinessRoleParams(comment="parsed") == convert_business_role({"comment": "parsed"})


def test_convert_business_role_error_extra_property():
    with pytest.raises(ValidationError) as ve:
        convert_business_role({
            "unexpected": "should fail"
        })
    ve.match(".*Unexpected keyword argument.*")


def test_convert_business_tech_role_alias():
    assert BusinessRoleParams(technical_roles=['T100']) == convert_business_role({"tech_roles": ["T100"]})
    assert BusinessRoleParams(technical_roles=['T1000']) == convert_business_role({"technical_roles": ["T1000"]})


def test_convert_business_role_error_tech_role_aliases():
    with pytest.raises(ValidationError) as ve:
        convert_business_role({
            "tech_roles": ["T100"],
            "technical_roles": ["T1000"]
        })

    ve.match("Only one of technical_roles and tech_roles properties is allowed in Business Role")
