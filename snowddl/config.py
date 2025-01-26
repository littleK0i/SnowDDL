from collections import defaultdict
from typing import Dict, List, Type, Optional, Union

from snowddl.blueprint import (
    AbstractBlueprint,
    AbstractIdentWithPrefix,
    AbstractPolicyReference,
    IdentPattern,
    ObjectType,
    PermissionModel,
    PermissionModelRuleset,
    PermissionModelCreateGrant,
    PermissionModelFutureGrant,
    T_Blueprint,
)


class SnowDDLConfig:
    DATABASE_ACCESS_ROLE_SUFFIX = "D_ROLE"
    SCHEMA_ACCESS_ROLE_SUFFIX = "S_ROLE"
    SHARE_ACCESS_ROLE_SUFFIX = "SH_ROLE"
    WAREHOUSE_ACCESS_ROLE_SUFFIX = "W_ROLE"

    BUSINESS_ROLE_SUFFIX = "B_ROLE"
    TECHNICAL_ROLE_SUFFIX = "T_ROLE"
    USER_ROLE_SUFFIX = "U_ROLE"

    OWNER_ROLE_TYPE = "OWNER"
    WRITE_ROLE_TYPE = "WRITE"
    READ_ROLE_TYPE = "READ"
    USAGE_ROLE_TYPE = "USAGE"
    MONITOR_ROLE_TYPE = "MONITOR"

    DEFAULT_PERMISSION_MODEL = "DEFAULT"

    def __init__(self, env_prefix=None):
        self.env_prefix = self._init_env_prefix(env_prefix)

        self.blueprints: Dict[Type[T_Blueprint], Dict[str, T_Blueprint]] = defaultdict(dict)
        self.placeholders: Dict[str, Union[bool, float, int, str]] = {}
        self.permission_models: Dict[str, PermissionModel] = self._init_permission_models()

    def get_blueprints_by_type(self, cls: Type[T_Blueprint]) -> Dict[str, T_Blueprint]:
        return self.blueprints.get(cls, {})

    def get_blueprints_by_type_and_pattern(self, cls: Type[T_Blueprint], pattern: IdentPattern) -> Dict[str, T_Blueprint]:
        return {full_name: bp for full_name, bp in self.blueprints.get(cls, {}).items() if pattern.is_match_ident(bp.full_name)}

    def get_placeholder(self, name: str) -> Union[bool, float, int, str, List[Union[bool, float, int, str]]]:
        if name not in self.placeholders:
            raise ValueError(f"Unknown placeholder [{name}]")

        return self.placeholders[name]

    def get_permission_model(self, name: Optional[str]) -> PermissionModel:
        if name is None:
            name = self.DEFAULT_PERMISSION_MODEL
        elif name not in self.permission_models:
            raise ValueError(f"Unknown permission model [{name}]")

        return self.permission_models[name]

    def add_blueprint(self, bp: AbstractBlueprint):
        self.blueprints[bp.__class__][str(bp.full_name)] = bp

    def remove_blueprint(self, bp: AbstractBlueprint):
        if str(bp.full_name) not in self.blueprints.get(bp.__class__, {}):
            raise ValueError(f"Blueprint with type [{bp.__class__.__name__}] and name [{bp.full_name}] does not exist in config")

        del self.blueprints[bp.__class__][str(bp.full_name)]

    def add_policy_reference(self, cls: Type[T_Blueprint], policy_name: AbstractIdentWithPrefix, ref: AbstractPolicyReference):
        if "references" not in cls.model_fields:
            raise ValueError(f"{cls.__name__} does not have field [references], probably not a policy")

        if str(policy_name) not in self.blueprints[cls]:
            raise ValueError(f"{cls.__name__} with name [{policy_name}] does not exist or was not defined yet")

        self.blueprints[cls][str(policy_name)].references.append(ref)

    def add_placeholder(self, name: str, value: Union[bool, float, int, str, List[Union[bool, float, int, str]]]):
        self.placeholders[name] = value

    def add_permission_model(self, name: str, permission_model: PermissionModel):
        self.permission_models[name] = permission_model

    def _init_env_prefix(self, env_prefix):
        if env_prefix:
            # Protects from code trying to use Config object and pass env prefix without separator at the end
            if not env_prefix.endswith(("__", "_", "$")):
                raise ValueError(
                    f"Env prefix [{env_prefix}] in identifier must end with valid separator like [__] double underscore, [_] single underscore or [$] dollar"
                )

            return env_prefix

        return ""

    def _init_permission_models(self):
        return {
            self.DEFAULT_PERMISSION_MODEL: PermissionModel(
                ruleset=PermissionModelRuleset.SCHEMA_OWNER,
                owner_create_grants=[
                    PermissionModelCreateGrant(on=ObjectType.FILE_FORMAT),
                    PermissionModelCreateGrant(on=ObjectType.FUNCTION),
                    PermissionModelCreateGrant(on=ObjectType.PROCEDURE),
                    PermissionModelCreateGrant(on=ObjectType.TABLE),
                    PermissionModelCreateGrant(on=ObjectType.VIEW),
                ],
                owner_future_grants=[
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.ALERT),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.DYNAMIC_TABLE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.EVENT_TABLE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.EXTERNAL_TABLE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.FILE_FORMAT),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.FUNCTION),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.MATERIALIZED_VIEW),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.PIPE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.PROCEDURE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.SEQUENCE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.STAGE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.STREAM),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.TABLE),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.TASK),
                    PermissionModelFutureGrant(privilege="OWNERSHIP", on=ObjectType.VIEW),
                ],
                write_future_grants=[
                    PermissionModelFutureGrant(privilege="READ", on=ObjectType.STAGE),
                    PermissionModelFutureGrant(privilege="WRITE", on=ObjectType.STAGE),
                    PermissionModelFutureGrant(privilege="USAGE", on=ObjectType.STAGE),
                    PermissionModelFutureGrant(privilege="USAGE", on=ObjectType.SEQUENCE),
                    PermissionModelFutureGrant(privilege="INSERT", on=ObjectType.TABLE),
                    PermissionModelFutureGrant(privilege="UPDATE", on=ObjectType.TABLE),
                    PermissionModelFutureGrant(privilege="DELETE", on=ObjectType.TABLE),
                    PermissionModelFutureGrant(privilege="TRUNCATE", on=ObjectType.TABLE),
                ],
                read_future_grants=[
                    PermissionModelFutureGrant(privilege="SELECT", on=ObjectType.DYNAMIC_TABLE),
                    PermissionModelFutureGrant(privilege="SELECT", on=ObjectType.EXTERNAL_TABLE),
                    PermissionModelFutureGrant(privilege="REFERENCES", on=ObjectType.EXTERNAL_TABLE),
                    PermissionModelFutureGrant(privilege="USAGE", on=ObjectType.FILE_FORMAT),
                    PermissionModelFutureGrant(privilege="USAGE", on=ObjectType.FUNCTION),
                    PermissionModelFutureGrant(privilege="SELECT", on=ObjectType.MATERIALIZED_VIEW),
                    PermissionModelFutureGrant(privilege="REFERENCES", on=ObjectType.MATERIALIZED_VIEW),
                    PermissionModelFutureGrant(privilege="USAGE", on=ObjectType.PROCEDURE),
                    PermissionModelFutureGrant(privilege="READ", on=ObjectType.STAGE),
                    PermissionModelFutureGrant(privilege="USAGE", on=ObjectType.STAGE),
                    PermissionModelFutureGrant(privilege="SELECT", on=ObjectType.STREAM),
                    PermissionModelFutureGrant(privilege="SELECT", on=ObjectType.TABLE),
                    PermissionModelFutureGrant(privilege="REFERENCES", on=ObjectType.TABLE),
                    PermissionModelFutureGrant(privilege="SELECT", on=ObjectType.VIEW),
                    PermissionModelFutureGrant(privilege="REFERENCES", on=ObjectType.VIEW),
                ],
            )
        }
