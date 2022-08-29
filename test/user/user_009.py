def test_009_step1(helper):
    user = helper.show_user("user_009")

    # Check each parameter
    assert str(user['login_name']).endswith('__JOHN_DOE')
    assert user['display_name'] == 'JDOE'
    assert user['first_name'] == 'John'
    assert user['last_name'] == 'Doe'
    assert user['email'] == 'john@example.com'
    assert user['disabled'] == 'false'

    assert user['has_password'] == 'false'
    assert user['has_rsa_public_key'] == 'true'

    assert str(user['default_namespace']).endswith('__DB1.SC1')
    assert str(user['default_warehouse']).endswith('__WAREHOUSE_009_01')

    # Empty comment
    assert not user['comment']


def test_009_step2(helper):
    user = helper.show_user("user_009")

    # Check each parameter
    assert str(user['login_name']).endswith('__GILL_GOE')
    assert user['display_name'] == 'GGOE'
    assert user['first_name'] == 'Gill'
    assert user['last_name'] == 'Goe'
    assert user['email'] == 'gill@example.com'
    assert user['disabled'] == 'true'

    assert user['has_password'] == 'false'
    assert user['has_rsa_public_key'] == 'false'

    assert str(user['default_namespace']).endswith('__DB1.SC2')
    assert str(user['default_warehouse']).endswith('__WAREHOUSE_009_02')

    # Non-empty comment
    assert user['comment']


def test_009_step3(helper):
    user = helper.show_user("user_009")

    # Sequence was dropped
    assert user is None
