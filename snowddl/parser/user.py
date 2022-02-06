from snowddl.blueprint import UserBlueprint, IdentWithPrefix
from snowddl.parser.abc_parser import AbstractParser
from snowddl.parser.business_role import business_role_json_schema


user_json_schema = {
    "type": "object",
    "properties": {
        "first_name": {
            "type": "string"
        },
        "last_name": {
            "type": "string"
        },
        "email": {
            "type": "string"
        },
        "disabled": {
            "type": "boolean"
        },
        "password": {
            "type": "string"
        },
        "rsa_public_key": {
            "type": "string"
        },
        "rsa_public_key_2": {
            "type": "string"
        },
        "default_warehouse": {
            "type": "string"
        },
        "default_namespace": {
            "type": "string"
        },
        "session_params": {
            "type": "object",
            "additionalParams": {
                "type": ["boolean", "number", "string"]
            }
        },
        "business_roles": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "comment": {
            "type": "string"
        }
    },
    "additionalParams": False
}


class UserParser(AbstractParser):
    def load_blueprints(self):
        user_config = self.parse_single_file(self.base_path / 'user.yaml', user_json_schema)
        default_warehouse_map = self.get_default_warehouse_map()

        for user_name, user in user_config.items():
            business_roles = []
            default_warehouse = user.get('default_warehouse')

            for business_role_name in user['business_roles']:
                business_roles.append(self.config.build_role_ident(business_role_name, self.config.BUSINESS_ROLE_SUFFIX))

                if default_warehouse is None:
                    default_warehouse = default_warehouse_map.get(business_role_name)

            bp = UserBlueprint(
                full_name=IdentWithPrefix(self.env_prefix, user_name),
                first_name=user.get('first_name'),
                last_name=user.get('last_name'),
                email=user.get('email'),
                disabled=user.get('disabled', False),
                password=user.get('password'),
                rsa_public_key=user.get('rsa_public_key').replace(' ', '') if user.get('rsa_public_key') else None,
                rsa_public_key_2=user.get('rsa_public_key_2').replace(' ', '') if user.get('rsa_public_key_2') else None,
                default_warehouse=self.config.build_complex_ident(default_warehouse) if default_warehouse else None,
                default_namespace=self.config.build_complex_ident(user.get('default_namespace')) if user.get('default_namespace') else None,
                session_params=self.normalise_params_dict(user.get('params', {})),
                business_roles=business_roles,
                comment=user.get('comment'),
            )

            self.config.add_blueprint(bp)

    def get_default_warehouse_map(self):
        default_warehouse_map = {}

        business_role_config = self.parse_single_file(self.base_path / 'business_role.yaml', business_role_json_schema)

        for business_role_name, business_role in business_role_config.items():
            if 'warehouse_usage' not in business_role:
                continue

            default_warehouse_map[business_role_name] = business_role['warehouse_usage'][0]

        return default_warehouse_map
