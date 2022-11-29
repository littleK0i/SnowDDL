def test_step1(helper):
    user = helper.show_user("us001_us1")
    user_params = helper.show_user_parameters("us001_us1")

    assert str(user['login_name']).endswith('__JOHN_DOE')
    assert user['display_name'] == 'JDOE'
    assert user['first_name'] == 'John'
    assert user['last_name'] == 'Doe'
    assert user['email'] == 'john@example.com'
    assert user['disabled'] == 'false'

    assert user['has_password'] == 'false'
    assert user['has_rsa_public_key'] == 'true'

    assert str(user['default_namespace']).endswith('__DB1.SC1')
    assert str(user['default_warehouse']).endswith('__US001_WH1')

    # Empty comment
    assert not user['comment']

    assert user_params['QUERY_TAG']['value'] == 'test'
    assert user_params['QUERY_TAG']['level'] == 'USER'

    assert user_params['ROWS_PER_RESULTSET']['value'] == '10000'
    assert user_params['ROWS_PER_RESULTSET']['level'] == 'USER'

    assert user_params['STRICT_JSON_OUTPUT']['value'] == 'true'
    assert user_params['STRICT_JSON_OUTPUT']['level'] == 'USER'


def test_step2(helper):
    user = helper.show_user("us001_us1")
    user_params = helper.show_user_parameters("us001_us1")

    assert str(user['login_name']).endswith('__GILL_GOE')
    assert user['display_name'] == 'GGOE'
    assert user['first_name'] == 'Gill'
    assert user['last_name'] == 'Goe'
    assert user['email'] == 'gill@example.com'
    assert user['disabled'] == 'true'

    assert user['has_password'] == 'false'
    assert user['has_rsa_public_key'] == 'false'

    assert str(user['default_namespace']).endswith('__DB1.SC2')
    assert str(user['default_warehouse']).endswith('__US001_WH2')

    # Non-empty comment
    assert user['comment']

    assert user_params['QUERY_TAG']['value'] == 'test1'
    assert user_params['QUERY_TAG']['level'] == 'USER'

    assert user_params['ROWS_PER_RESULTSET']['value'] == '100000'
    assert user_params['ROWS_PER_RESULTSET']['level'] == 'USER'

    assert user_params['STRICT_JSON_OUTPUT']['level'] == ''


def test_step3(helper):
    user = helper.show_user("us001_us1")

    # Sequence was dropped
    assert user is None
