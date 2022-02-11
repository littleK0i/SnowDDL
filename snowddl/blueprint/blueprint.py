from abc import ABC
from dataclasses import dataclass
from typing import Optional, List, Dict, Union, TypeVar, TYPE_CHECKING

from .column import ExternalTableColumn, TableColumn, ViewColumn, NameWithType
from .data_type import BaseDataType, DataType
from .grant import Grant, FutureGrant
from .ident import Ident, IdentWithPrefix, ComplexIdentWithPrefix, ComplexIdentWithPrefixAndArgs
from .reference import MaskingPolicyReference, RowAccessPolicyReference, TagReference

if TYPE_CHECKING:
    from .object_type import ObjectType


@dataclass
class AbstractBlueprint(ABC):
    full_name: Ident
    comment: Optional[str]


@dataclass
class SchemaObjectBlueprint(AbstractBlueprint, ABC):
    full_name: ComplexIdentWithPrefix
    database: IdentWithPrefix
    schema: Ident
    name: Ident


@dataclass
class RoleBlueprint(AbstractBlueprint):
    full_name: IdentWithPrefix
    grants: List[Grant]
    future_grants: List[FutureGrant]


@dataclass
class DependsOnMixin(ABC):
    full_name: Ident
    depends_on: List[Ident]


@dataclass
class AccountParameterBlueprint(AbstractBlueprint):
    value: Union[bool,float,int,str]


@dataclass
class BusinessRoleBlueprint(RoleBlueprint):
    pass


@dataclass
class DatabaseBlueprint(AbstractBlueprint):
    full_name: IdentWithPrefix
    database: IdentWithPrefix
    is_transient: Optional[bool]
    retention_time: Optional[int]


@dataclass
class ExternalTableBlueprint(SchemaObjectBlueprint):
    columns: Optional[List[ExternalTableColumn]]
    partition_by: Optional[List[Ident]]
    location_stage: ComplexIdentWithPrefix
    location_path: Optional[str]
    location_pattern: Optional[str]
    file_format: ComplexIdentWithPrefix
    refresh_on_create: Optional[bool]
    auto_refresh: Optional[bool]
    aws_sns_topic: Optional[str]
    integration: Optional[Ident]


@dataclass
class FileFormatBlueprint(SchemaObjectBlueprint):
    type: str
    format_options: Optional[Dict[str,Union[bool,float,int,str,list]]]


@dataclass
class ForeignKeyBlueprint(AbstractBlueprint):
    table_name: ComplexIdentWithPrefix
    columns: List[Ident]
    ref_table_name: ComplexIdentWithPrefix
    ref_columns: List[Ident]


@dataclass
class FunctionBlueprint(SchemaObjectBlueprint):
    full_name: ComplexIdentWithPrefixAndArgs
    language: str
    body: str
    arguments: List[NameWithType]
    returns: Union[DataType,List[NameWithType]]
    is_secure: bool
    is_strict: bool
    is_immutable: bool


@dataclass
class MaterializedViewBlueprint(SchemaObjectBlueprint):
    text: str
    columns: Optional[List[ViewColumn]]
    is_secure: Optional[bool]
    cluster_by: Optional[List[str]]


@dataclass
class MaskingPolicyBlueprint(SchemaObjectBlueprint):
    full_name: ComplexIdentWithPrefix
    arguments: List[NameWithType]
    returns: DataType
    body: str
    references: List[MaskingPolicyReference]


@dataclass
class NetworkPolicyBlueprint(AbstractBlueprint):
    full_name: Ident
    allowed_ip_list: List[str]
    blocked_ip_list: List[str]


@dataclass
class PipeBlueprint(SchemaObjectBlueprint):
    auto_ingest: bool
    copy_table_name: ComplexIdentWithPrefix
    copy_stage_name: ComplexIdentWithPrefix
    copy_path: Optional[str]
    copy_pattern: Optional[str]
    copy_transform: Optional[Dict[str, str]]
    copy_file_format: Optional[ComplexIdentWithPrefix]
    copy_options: Optional[Dict[str,Union[bool,float,int,str,list]]]
    aws_sns_topic: Optional[str]
    integration: Optional[Ident]


@dataclass
class PrimaryKeyBlueprint(AbstractBlueprint):
    table_name: ComplexIdentWithPrefix
    columns: List[Ident]


@dataclass
class ProcedureBlueprint(SchemaObjectBlueprint):
    full_name: ComplexIdentWithPrefixAndArgs
    language: str
    body: str
    arguments: List[NameWithType]
    returns: DataType
    is_strict: bool
    is_immutable: bool
    is_execute_as_caller: bool


@dataclass
class RowAccessPolicyBlueprint(SchemaObjectBlueprint):
    full_name: ComplexIdentWithPrefix
    arguments: List[NameWithType]
    body: str
    references: List[RowAccessPolicyReference]


@dataclass
class SchemaBlueprint(AbstractBlueprint):
    full_name: ComplexIdentWithPrefix
    database: IdentWithPrefix
    schema: Ident
    is_transient: Optional[bool]
    retention_time: Optional[int]
    is_sandbox: Optional[bool]


@dataclass
class StageBlueprint(SchemaObjectBlueprint):
    url: Optional[str]
    storage_integration: Optional[Ident]
    encryption: Optional[Dict[str,str]]
    directory: Optional[Dict[str,str]]
    file_format: Optional[ComplexIdentWithPrefix]
    copy_options: Optional[Dict[str,Union[bool,float,int,str,list]]]


@dataclass
class SequenceBlueprint(SchemaObjectBlueprint):
    start: int
    interval: int


@dataclass
class StreamBlueprint(SchemaObjectBlueprint):
    object_type: "ObjectType"
    object_name: ComplexIdentWithPrefix
    append_only: Optional[bool]
    insert_only: Optional[bool]
    show_initial_rows: Optional[bool]


@dataclass
class TableBlueprint(SchemaObjectBlueprint):
    columns: List[TableColumn]
    cluster_by: Optional[List[str]]
    is_transient: bool
    retention_time: Optional[int]
    change_tracking: bool
    search_optimization: bool


@dataclass
class TagBlueprint(SchemaObjectBlueprint):
    full_name: ComplexIdentWithPrefix
    references: List[TagReference]


@dataclass
class TaskBlueprint(SchemaObjectBlueprint, DependsOnMixin):
    body: str
    schedule: Optional[str]
    after: Optional[Ident]
    when: Optional[str]
    warehouse: Optional[IdentWithPrefix]
    user_task_managed_initial_warehouse_size: Optional[str]
    allow_overlapping_execution: Optional[bool]
    session_params: Optional[Dict[str,Union[bool,float,int,str]]]
    user_task_timeout_ms: Optional[int]


@dataclass
class TechRoleBlueprint(RoleBlueprint):
    pass


@dataclass
class UniqueKeyBlueprint(AbstractBlueprint):
    table_name: ComplexIdentWithPrefix
    columns: List[Ident]


@dataclass
class UserBlueprint(AbstractBlueprint):
    full_name: IdentWithPrefix
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    disabled: bool
    business_roles: List[IdentWithPrefix]
    password: Optional[str]
    rsa_public_key: Optional[str]
    rsa_public_key_2: Optional[str]
    default_warehouse: Optional[ComplexIdentWithPrefix]
    default_namespace: Optional[ComplexIdentWithPrefix]
    session_params: Optional[Dict[str,Union[bool,float,int,str]]]


@dataclass
class ViewBlueprint(SchemaObjectBlueprint, DependsOnMixin):
    text: str
    columns: Optional[List[ViewColumn]]
    is_secure: Optional[bool]


@dataclass
class WarehouseBlueprint(AbstractBlueprint):
    full_name: IdentWithPrefix
    size: str
    auto_suspend: int
    min_cluster_count: Optional[int]
    max_cluster_count: Optional[int]
    scaling_policy: Optional[str]
    resource_monitor: Optional[Ident]


T_Blueprint = TypeVar('T_Blueprint', bound=AbstractBlueprint)
