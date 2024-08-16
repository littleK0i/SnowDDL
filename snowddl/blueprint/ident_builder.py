from typing import Union

from .data_type import BaseDataType
from .ident import (
    AccountObjectIdent,
    DatabaseIdent,
    DatabaseRoleIdent,
    SchemaIdent,
    SchemaObjectIdent,
    SchemaObjectIdentWithArgs,
)
from .object_type import ObjectType


def build_schema_object_ident(env_prefix, object_name, context_database_name, context_schema_name) -> SchemaObjectIdent:
    # Function or procedure identifier with arguments
    if object_name.endswith(")"):
        object_name, data_types_str = object_name.rstrip(")").split("(")
        data_types = [BaseDataType[dt.strip(" ").upper()] for dt in data_types_str.split(",")] if data_types_str else []
    else:
        data_types = None

    parts = object_name.split(".")
    parts_len = len(parts)

    if parts_len > 3:
        raise ValueError(f"Too many delimiters in schema object identifier [{object_name}]")

    # Add context db_name to "schema_name.object_name" or "object_name" identifier
    if parts_len <= 2:
        parts.insert(0, context_database_name)

    # Add context schema_name to "object_name" identifier
    if parts_len == 1:
        parts.insert(1, context_schema_name)

    # Function or procedure identifier with arguments
    if isinstance(data_types, list):
        return SchemaObjectIdentWithArgs(env_prefix, parts[0], parts[1], parts[2], data_types=data_types)

    return SchemaObjectIdent(env_prefix, parts[0], parts[1], parts[2])


def build_role_ident(env_prefix, *args: Union[AccountObjectIdent, str]) -> AccountObjectIdent:
    return AccountObjectIdent(
        env_prefix, f"{'__'.join(str(a.name) if isinstance(a, AccountObjectIdent) else str(a) for a in args)}"
    )


def build_grant_name_ident(object_type: ObjectType, grant_name: str):
    env_prefix = ""

    parts = [p.strip('"') for p in grant_name.split(".")]
    last_part = parts[-1]

    if len(parts) == 3:
        # Extract data types from arguments of FUNCTION or PROCEDURE
        if object_type.is_overloading_supported:
            start_dtypes_idx = last_part.index("(")
            finish_dtypes_idx = last_part.index(")")

            parts[-1] = last_part[0:start_dtypes_idx]
            arguments_str = last_part[start_dtypes_idx + 1 : finish_dtypes_idx]
            data_types = []

            if arguments_str:
                for arg in arguments_str.split(","):
                    data_types.append(BaseDataType[arg.strip(" ").split(" ")[-1]])

            return SchemaObjectIdentWithArgs(env_prefix, parts[0], parts[1], parts[2], data_types=data_types)

        return SchemaObjectIdent(env_prefix, parts[0], parts[1], parts[2])

    if len(parts) == 2:
        if object_type == ObjectType.DATABASE_ROLE:
            return DatabaseRoleIdent(env_prefix, parts[0], parts[1])

        return SchemaIdent(env_prefix, parts[0], parts[1])

    if len(parts) == 1:
        if object_type == ObjectType.DATABASE:
            return DatabaseIdent(env_prefix, parts[0])

        return AccountObjectIdent(env_prefix, parts[0])

    raise ValueError(f"Unexpected grant name format [{grant_name}] in Snowflake for object type [{object_type}]")


def build_future_grant_name_ident(object_type: ObjectType, grant_name: str):
    env_prefix = ""

    parts = [p.strip('"') for p in grant_name.split(".")]
    parts.pop()  # Remove object type component from future grant names

    if len(parts) == 2:
        return SchemaIdent(env_prefix, parts[0], parts[1])

    if len(parts) == 1:
        return DatabaseIdent(env_prefix, parts[0])

    raise ValueError(f"Unexpected grant name format [{grant_name}] in Snowflake for object type [{object_type}]")


def build_default_namespace_ident(env_prefix, default_namespace):
    if "." in default_namespace:
        return SchemaIdent(env_prefix, *default_namespace.split(".", 1))

    return DatabaseIdent(env_prefix, default_namespace)
