from functools import partial

from snowddl.blueprint import (
    UserBlueprint,
    AccountObjectIdent,
    AuthenticationPolicyBlueprint,
    AuthenticationPolicyReference,
    NetworkPolicyBlueprint,
    NetworkPolicyReference,
    ObjectType,
    SchemaObjectIdent,
    build_role_ident,
    build_default_namespace_ident,
)
from snowddl.parser.abc_parser import AbstractParser
from snowddl.parser.business_role import business_role_json_schema


# fmt: off
user_json_schema = {
    "type": "object",
    "additionalProperties": {
        "properties": {
            "login_name": {
                "type": "string"
            },
            "display_name": {
                "type": "string"
            },
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
            "type": {
                "type": "string",
            },
            "default_warehouse": {
                "type": "string"
            },
            "default_namespace": {
                "type": "string"
            },
            "session_params": {
                "type": "object",
                "additionalProperties": {
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
            },
            "authentication_policy": {
                "type": "string",
            },
            "network_policy": {
                "type": "string",
            },
        },
        "additionalProperties": False
    }
}
# fmt: on


class UserParser(AbstractParser):
    def load_blueprints(self):
        default_wh_map = self.get_default_warehouse_map()

        self.parse_multi_entity_file("user", user_json_schema, partial(self.process_user, default_wh_map=default_wh_map))

    def process_user(self, user_name, user_params, default_wh_map):
        business_roles = []
        default_warehouse = user_params.get("default_warehouse")

        for business_role_name in user_params.get("business_roles", []):
            business_roles.append(build_role_ident(self.env_prefix, business_role_name, self.config.BUSINESS_ROLE_SUFFIX))

            if default_warehouse is None:
                default_warehouse = default_wh_map.get(business_role_name)

        full_user_name = AccountObjectIdent(self.env_prefix, user_name)

        if user_params.get("login_name"):
            # Login name is string, not identifier (!), special characters like '@#!' are permitted
            # But it still requires env_prefix due to unique constraint
            login_name = f"{self.config.env_prefix}{user_params.get('login_name')}".upper()
        else:
            login_name = str(full_user_name)

        if user_params.get("display_name"):
            display_name = str(user_params.get("display_name")).upper()
        else:
            display_name = str(full_user_name)

        # fmt: off
        bp = UserBlueprint(
            full_name=full_user_name,
            login_name=login_name,
            display_name=display_name,
            first_name=user_params.get("first_name"),
            last_name=user_params.get("last_name"),
            email=user_params.get("email"),
            disabled=user_params.get("disabled", False),
            password=user_params.get("password"),
            rsa_public_key=user_params.get("rsa_public_key").replace(" ", "") if user_params.get("rsa_public_key") else None,
            rsa_public_key_2=user_params.get("rsa_public_key_2").replace(" ", "") if user_params.get("rsa_public_key_2") else None,
            type=str(user_params.get("type")).upper() if user_params.get("type") else None,
            default_warehouse=AccountObjectIdent(self.env_prefix, default_warehouse) if default_warehouse else None,
            default_namespace=build_default_namespace_ident(self.env_prefix, user_params.get("default_namespace")) if user_params.get("default_namespace") else None,
            session_params=self.normalise_params_dict(user_params.get("session_params", {})),
            business_roles=business_roles,
            comment=user_params.get("comment"),
        )
        # fmt: on

        self.config.add_blueprint(bp)

        # Authentication policy
        if user_params.get("authentication_policy"):
            policy_name_parts = user_params.get("authentication_policy").split(".")

            if len(policy_name_parts) != 3:
                raise ValueError(
                    f"Authentication policy [{user_params.get('authentication_policy')}] should use fully-qualified identifier <database>.<schema>.<name> for user [{full_user_name}]"
                )

            policy_name = SchemaObjectIdent(self.env_prefix, *policy_name_parts)

            ref = AuthenticationPolicyReference(
                object_type=ObjectType.USER,
                object_name=full_user_name,
            )

            self.config.add_policy_reference(AuthenticationPolicyBlueprint, policy_name, ref)

        # Network policy
        if user_params.get("network_policy"):
            policy_name = AccountObjectIdent(self.env_prefix, user_params.get("network_policy"))

            ref = NetworkPolicyReference(
                object_type=ObjectType.USER,
                object_name=full_user_name,
            )

            self.config.add_policy_reference(NetworkPolicyBlueprint, policy_name, ref)

        if "NETWORK_POLICY" in bp.session_params:
            raise ValueError(
                "NETWORK_POLICY in session_params of USER is no longer supported. Please use dedicated [network_policy] parameter instead. Read more: https://docs.snowddl.com/breaking-changes-log/0.33.0-october-2024"
            )

    def get_default_warehouse_map(self):
        default_warehouse_map = {}

        business_role_config = self.parse_single_entity_file("business_role", business_role_json_schema)

        for business_role_name, business_role in business_role_config.items():
            if "warehouse_usage" not in business_role:
                continue

            default_warehouse_map[business_role_name] = business_role["warehouse_usage"][0]

        return default_warehouse_map
