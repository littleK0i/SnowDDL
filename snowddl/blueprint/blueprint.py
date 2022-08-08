from abc import ABC
from dataclasses import dataclass
from typing import Optional, List, Dict, Union, TypeVar, TYPE_CHECKING

from .column import ExternalTableColumn, TableColumn, ViewColumn, NameWithType
from .data_type import DataType
from .grant import Grant, FutureGrant
from .ident import AbstractIdent, Ident, AccountObjectIdent, DatabaseIdent, AccountIdent, InboundShareIdent, OutboundShareIdent, SchemaIdent, SchemaObjectIdent, SchemaObjectIdentWithArgs, StageFileIdent, TableConstraintIdent
from .reference import MaskingPolicyReference, RowAccessPolicyReference, TagReference
from .stage import StageWithPath

if TYPE_CHECKING:
    from .object_type import ObjectType


@dataclass
class AbstractBlueprint(ABC):
    full_name: AbstractIdent
    comment: Optional[str]


@dataclass
class SchemaObjectBlueprint(AbstractBlueprint, ABC):
    full_name: SchemaObjectIdent


@dataclass
class RoleBlueprint(AbstractBlueprint):
    full_name: AccountObjectIdent
    grants: List[Grant]
    future_grants: List[FutureGrant]


@dataclass
class DependsOnMixin(ABC):
    full_name: AbstractIdent
    depends_on: List[AbstractIdent]


@dataclass
class AccountParameterBlueprint(AbstractBlueprint):
    full_name: Ident
    value: Union[bool,float,int,str]


@dataclass
class BusinessRoleBlueprint(RoleBlueprint):
    pass


@dataclass
class DatabaseBlueprint(AbstractBlueprint):
    full_name: DatabaseIdent
    is_transient: Optional[bool]
    retention_time: Optional[int]
    is_sandbox: Optional[bool]


@dataclass
class DatabaseShareBlueprint(AbstractBlueprint):
    full_name: DatabaseIdent
    share_name: InboundShareIdent


@dataclass
class ExternalFunctionBlueprint(SchemaObjectBlueprint):
    full_name: SchemaObjectIdent
    arguments: List[NameWithType]
    returns: DataType
    api_integration: Ident
    url: str
    is_secure: bool
    is_strict: bool
    is_immutable: bool
    headers: Optional[Dict[str,str]]
    context_headers: Optional[List[Ident]]
    max_batch_rows: Optional[int]
    compression: Optional[str]
    request_translator: Optional[SchemaObjectIdent]
    response_translator: Optional[SchemaObjectIdent]


@dataclass
class ExternalTableBlueprint(SchemaObjectBlueprint):
    columns: Optional[List[ExternalTableColumn]]
    partition_by: Optional[List[Ident]]
    partition_type: Optional[str]
    location_stage: SchemaObjectIdent
    location_path: Optional[str]
    location_pattern: Optional[str]
    file_format: SchemaObjectIdent
    refresh_on_create: Optional[bool]
    auto_refresh: Optional[bool]
    aws_sns_topic: Optional[str]
    table_format: Optional[str]
    integration: Optional[Ident]


@dataclass
class FileFormatBlueprint(SchemaObjectBlueprint):
    type: str
    format_options: Optional[Dict[str,Union[bool,float,int,str,list]]]


@dataclass
class ForeignKeyBlueprint(SchemaObjectBlueprint):
    full_name: TableConstraintIdent
    table_name: SchemaObjectIdent
    columns: List[Ident]
    ref_table_name: SchemaObjectIdent
    ref_columns: List[Ident]


@dataclass
class FunctionBlueprint(SchemaObjectBlueprint):
    full_name: SchemaObjectIdentWithArgs
    language: str
    body: Optional[str]
    arguments: List[NameWithType]
    returns: Union[DataType,List[NameWithType]]
    is_secure: bool
    is_strict: bool
    is_immutable: bool
    runtime_version: Optional[str]
    imports: Optional[List[StageWithPath]]
    packages: Optional[List[str]]
    handler: Optional[str]


@dataclass
class InboundShareBlueprint(AbstractBlueprint):
    full_name: DatabaseIdent
    accounts: List[AccountIdent]
    share_restrictions: bool
    grants: List[Grant]


@dataclass
class MaterializedViewBlueprint(SchemaObjectBlueprint):
    text: str
    columns: Optional[List[ViewColumn]]
    is_secure: Optional[bool]
    cluster_by: Optional[List[str]]


@dataclass
class MaskingPolicyBlueprint(SchemaObjectBlueprint):
    full_name: SchemaObjectIdent
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
class OutboundShareBlueprint(AbstractBlueprint):
    full_name: OutboundShareIdent
    accounts: List[AccountIdent]
    share_restrictions: Optional[bool]
    grants: List[Grant]


@dataclass
class PipeBlueprint(SchemaObjectBlueprint):
    auto_ingest: bool
    copy_table_name: SchemaObjectIdent
    copy_stage_name: SchemaObjectIdent
    copy_path: Optional[str]
    copy_pattern: Optional[str]
    copy_transform: Optional[Dict[str, str]]
    copy_file_format: Optional[SchemaObjectIdent]
    copy_options: Optional[Dict[str,Union[bool,float,int,str,list]]]
    aws_sns_topic: Optional[str]
    integration: Optional[Ident]


@dataclass
class PrimaryKeyBlueprint(SchemaObjectBlueprint):
    full_name: TableConstraintIdent
    table_name: SchemaObjectIdent
    columns: List[Ident]


@dataclass
class ProcedureBlueprint(SchemaObjectBlueprint):
    full_name: SchemaObjectIdentWithArgs
    language: str
    body: str
    arguments: List[NameWithType]
    returns: Union[DataType,List[NameWithType]]
    is_strict: bool
    is_immutable: bool
    is_execute_as_caller: bool
    runtime_version: Optional[str]
    imports: Optional[List[StageWithPath]]
    packages: Optional[List[str]]
    handler: Optional[str]


@dataclass
class ResourceMonitorBlueprint(AbstractBlueprint):
    full_name: Ident
    credit_quota: int
    frequency: str
    triggers: Dict[int,str]


@dataclass
class RowAccessPolicyBlueprint(SchemaObjectBlueprint):
    full_name: SchemaObjectIdent
    arguments: List[NameWithType]
    body: str
    references: List[RowAccessPolicyReference]


@dataclass
class SchemaBlueprint(AbstractBlueprint):
    full_name: SchemaIdent
    is_transient: Optional[bool]
    retention_time: Optional[int]
    is_sandbox: Optional[bool]
    owner_additional_grants: List[Grant]


@dataclass
class SchemaRoleBlueprint(RoleBlueprint, DependsOnMixin):
    pass


@dataclass
class StageBlueprint(SchemaObjectBlueprint):
    url: Optional[str]
    storage_integration: Optional[Ident]
    encryption: Optional[Dict[str,str]]
    directory: Optional[Dict[str,str]]
    file_format: Optional[SchemaObjectIdent]
    copy_options: Optional[Dict[str,Union[bool,float,int,str,list]]]
    upload_stage_files: bool


@dataclass
class StageFileBlueprint(SchemaObjectBlueprint):
    full_name: StageFileIdent
    local_path: str
    stage_name: SchemaObjectIdent
    stage_path: str


@dataclass
class SequenceBlueprint(SchemaObjectBlueprint):
    start: int
    interval: int


@dataclass
class StreamBlueprint(SchemaObjectBlueprint):
    object_type: "ObjectType"
    object_name: SchemaObjectIdent
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
    full_name: SchemaObjectIdent
    references: List[TagReference]


@dataclass
class TaskBlueprint(SchemaObjectBlueprint, DependsOnMixin):
    body: str
    schedule: Optional[str]
    after: Optional[List[SchemaObjectIdent]]
    when: Optional[str]
    warehouse: Optional[AccountObjectIdent]
    user_task_managed_initial_warehouse_size: Optional[str]
    allow_overlapping_execution: Optional[bool]
    session_params: Optional[Dict[str,Union[bool,float,int,str]]]
    user_task_timeout_ms: Optional[int]


@dataclass
class TechRoleBlueprint(RoleBlueprint):
    pass


@dataclass
class UniqueKeyBlueprint(SchemaObjectBlueprint):
    full_name: TableConstraintIdent
    table_name: SchemaObjectIdent
    columns: List[Ident]


@dataclass
class UserBlueprint(AbstractBlueprint):
    full_name: AccountObjectIdent
    login_name: str
    display_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    disabled: bool
    business_roles: List[AccountObjectIdent]
    password: Optional[str]
    rsa_public_key: Optional[str]
    rsa_public_key_2: Optional[str]
    default_warehouse: Optional[AccountObjectIdent]
    default_namespace: Optional[Union[DatabaseIdent, SchemaIdent]]
    session_params: Optional[Dict[str,Union[bool,float,int,str]]]


@dataclass
class ViewBlueprint(SchemaObjectBlueprint, DependsOnMixin):
    text: str
    columns: Optional[List[ViewColumn]]
    is_secure: Optional[bool]


@dataclass
class WarehouseBlueprint(AbstractBlueprint):
    full_name: AccountObjectIdent
    size: str
    auto_suspend: int
    min_cluster_count: Optional[int]
    max_cluster_count: Optional[int]
    scaling_policy: Optional[str]
    resource_monitor: Optional[Ident]


T_Blueprint = TypeVar('T_Blueprint', bound=AbstractBlueprint)
