from abc import ABC
from pathlib import Path
from typing import Optional, List, Dict, Set, Union, TypeVar

from .column import (
    DynamicTableColumn,
    ExternalTableColumn,
    TableColumn,
    ViewColumn,
    ArgumentWithType,
    NameWithType,
    SearchOptimizationItem,
)
from .data_type import DataType
from .grant import AccountGrant, Grant, FutureGrant, GrantPattern
from .ident import (
    AbstractIdent,
    Ident,
    AccountObjectIdent,
    DatabaseIdent,
    DatabaseRoleIdent,
    AccountIdent,
    OutboundShareIdent,
    SchemaIdent,
    SchemaObjectIdent,
    SchemaObjectIdentWithArgs,
    StageFileIdent,
    TableConstraintIdent,
)
from .ident_pattern import IdentPattern
from .object_type import ObjectType
from .reference import (
    AggregationPolicyReference,
    AuthenticationPolicyReference,
    ForeignKeyReference,
    IndexReference,
    MaskingPolicyReference,
    NetworkPolicyReference,
    ProjectionPolicyReference,
    RowAccessPolicyReference,
    TagReference,
)
from .stage import StageWithPath
from ..model import BaseModelWithConfig


class DependsOnMixin(BaseModelWithConfig, ABC):
    depends_on: Set[AbstractIdent] = set()


class AbstractBlueprint(BaseModelWithConfig, ABC):
    full_name: AbstractIdent
    comment: Optional[str] = None


class SchemaObjectBlueprint(AbstractBlueprint, ABC):
    full_name: SchemaObjectIdent


class RoleBlueprint(AbstractBlueprint, DependsOnMixin):
    full_name: AccountObjectIdent
    grants: List[Grant] = []
    account_grants: List[AccountGrant] = []
    future_grants: List[FutureGrant] = []


class AccountParameterBlueprint(AbstractBlueprint):
    full_name: Ident
    value: Union[bool, float, int, str]


class AggregationPolicyBlueprint(SchemaObjectBlueprint):
    body: str
    references: List[AggregationPolicyReference] = []


class AlertBlueprint(SchemaObjectBlueprint):
    full_name: SchemaObjectIdent
    warehouse: Optional[AccountObjectIdent] = None
    schedule: str
    condition: str
    action: str


class AuthenticationPolicyBlueprint(SchemaObjectBlueprint):
    authentication_methods: List[str]
    mfa_authentication_methods: List[str]
    mfa_enrollment: str
    client_types: List[str]
    security_integrations: List[str]
    references: List[AuthenticationPolicyReference] = []


class BusinessRoleBlueprint(AbstractBlueprint):
    full_name: AccountObjectIdent
    database_owner: List[IdentPattern] = []
    database_write: List[IdentPattern] = []
    database_read: List[IdentPattern] = []
    schema_owner: List[IdentPattern] = []
    schema_write: List[IdentPattern] = []
    schema_read: List[IdentPattern] = []
    share_read: List[Union[Ident, DatabaseRoleIdent]] = []
    warehouse_usage: List[AccountObjectIdent] = []
    warehouse_monitor: List[AccountObjectIdent] = []
    technical_roles: List[AccountObjectIdent] = []
    global_roles: List[Ident] = []


class DatabaseBlueprint(AbstractBlueprint):
    full_name: DatabaseIdent
    permission_model: Optional[str] = None
    is_sandbox: Optional[bool] = None
    is_transient: Optional[bool] = None
    retention_time: Optional[int] = None
    owner_database_write: List[IdentPattern] = []
    owner_database_read: List[IdentPattern] = []
    owner_integration_usage: List[Ident] = []
    owner_share_read: List[Union[Ident, DatabaseRoleIdent]] = []
    owner_warehouse_usage: List[AccountObjectIdent] = []
    owner_account_grants: List[AccountGrant] = []
    owner_global_roles: List[Ident] = []


class DynamicTableBlueprint(SchemaObjectBlueprint, DependsOnMixin):
    text: str
    columns: Optional[List[DynamicTableColumn]] = None
    target_lag: str
    warehouse: AccountObjectIdent
    refresh_mode: Optional[str] = None
    initialize: Optional[str] = None
    cluster_by: Optional[List[str]] = None
    is_transient: bool = False
    retention_time: Optional[int] = None


class EventTableBlueprint(SchemaObjectBlueprint):
    change_tracking: bool = False


class ExternalAccessIntegrationBlueprint(AbstractBlueprint):
    full_name: AccountObjectIdent
    allowed_network_rules: List[SchemaObjectIdent]
    allowed_api_authentication_integrations: Optional[List[Ident]] = None
    allowed_authentication_secrets: Optional[List[SchemaObjectIdent]] = None
    enabled: bool = True


class ExternalFunctionBlueprint(SchemaObjectBlueprint):
    full_name: SchemaObjectIdent
    arguments: List[NameWithType]
    returns: DataType
    api_integration: Ident
    url: str
    is_secure: bool = False
    is_strict: bool = False
    is_immutable: bool = False
    headers: Optional[Dict[str, str]] = None
    context_headers: Optional[List[Ident]] = None
    max_batch_rows: Optional[int] = None
    compression: Optional[str] = None
    request_translator: Optional[SchemaObjectIdent] = None
    response_translator: Optional[SchemaObjectIdent] = None


class ExternalTableBlueprint(SchemaObjectBlueprint):
    columns: Optional[List[ExternalTableColumn]] = None
    partition_by: Optional[List[Ident]] = None
    partition_type: Optional[str] = None
    location_stage: SchemaObjectIdent
    location_path: Optional[str] = None
    location_pattern: Optional[str] = None
    file_format: SchemaObjectIdent
    refresh_on_create: Optional[bool] = None
    auto_refresh: Optional[bool] = None
    aws_sns_topic: Optional[str] = None
    table_format: Optional[str] = None
    integration: Optional[Ident] = None


class FileFormatBlueprint(SchemaObjectBlueprint):
    type: str
    format_options: Dict[str, Union[bool, float, int, str, list]] = {}


class ForeignKeyBlueprint(SchemaObjectBlueprint):
    full_name: TableConstraintIdent
    table_name: SchemaObjectIdent
    columns: List[Ident]
    ref_table_name: SchemaObjectIdent
    ref_columns: List[Ident]


class FunctionBlueprint(SchemaObjectBlueprint):
    full_name: SchemaObjectIdentWithArgs
    language: str
    body: Optional[str] = None
    arguments: List[ArgumentWithType]
    returns: Union[DataType, List[NameWithType]]
    is_secure: bool = False
    is_strict: bool = False
    is_immutable: bool = False
    is_memoizable: bool = False
    runtime_version: Optional[str] = None
    imports: Optional[List[StageWithPath]] = None
    packages: Optional[List[str]] = None
    handler: Optional[str] = None
    external_access_integrations: Optional[List[AccountObjectIdent]] = None
    secrets: Optional[Dict[str, SchemaObjectIdent]] = None


class HybridTableBlueprint(SchemaObjectBlueprint, DependsOnMixin):
    columns: List[TableColumn]
    primary_key: List[Ident]
    unique_keys: Optional[List[List[Ident]]] = None
    foreign_keys: Optional[List[ForeignKeyReference]] = None
    indexes: Optional[List[IndexReference]] = None


class IcebergTableBlueprint(SchemaObjectBlueprint):
    external_volume: Ident
    catalog: Ident
    catalog_table_name: Optional[str] = None
    catalog_namespace: Optional[str] = None
    metadata_file_path: Optional[str] = None
    base_location: Optional[str] = None
    replace_invalid_characters: bool = False
    auto_refresh: bool = False


class MaterializedViewBlueprint(SchemaObjectBlueprint):
    text: str
    columns: Optional[List[ViewColumn]] = None
    is_secure: bool = False
    cluster_by: Optional[List[str]] = None


class MaskingPolicyBlueprint(SchemaObjectBlueprint):
    arguments: List[NameWithType]
    returns: DataType
    body: str
    exempt_other_policies: bool = False
    references: List[MaskingPolicyReference] = []


class NetworkPolicyBlueprint(AbstractBlueprint):
    full_name: AccountObjectIdent
    allowed_network_rule_list: List[SchemaObjectIdent] = []
    blocked_network_rule_list: List[SchemaObjectIdent] = []
    allowed_ip_list: List[str] = []
    blocked_ip_list: List[str] = []
    references: List[NetworkPolicyReference] = []


class NetworkRuleBlueprint(SchemaObjectBlueprint):
    type: str
    value_list: List[str]
    mode: str


class OutboundShareBlueprint(AbstractBlueprint):
    full_name: OutboundShareIdent
    accounts: List[AccountIdent] = []
    share_restrictions: Optional[bool] = None
    grant_patterns: List[GrantPattern] = []


class PipeBlueprint(SchemaObjectBlueprint):
    auto_ingest: bool
    copy_table_name: SchemaObjectIdent
    copy_stage_name: SchemaObjectIdent
    copy_path: Optional[str] = None
    copy_pattern: Optional[str] = None
    copy_transform: Optional[Dict[str, str]] = None
    copy_file_format: Optional[SchemaObjectIdent] = None
    copy_match_by_column_name: Optional[str] = None
    copy_include_metadata: Optional[Dict[Ident, Ident]] = None
    copy_options: Optional[Dict[str, Union[bool, float, int, str, list]]] = None
    aws_sns_topic: Optional[str] = None
    integration: Optional[Ident] = None
    error_integration: Optional[Ident] = None


class PrimaryKeyBlueprint(SchemaObjectBlueprint):
    table_name: SchemaObjectIdent
    columns: List[Ident]


class ProcedureBlueprint(SchemaObjectBlueprint):
    full_name: SchemaObjectIdentWithArgs
    language: str
    body: Optional[str] = None
    arguments: List[ArgumentWithType]
    returns: Union[DataType, List[NameWithType]]
    is_strict: bool = False
    is_immutable: bool = False
    is_execute_as_caller: bool = False
    runtime_version: Optional[str] = None
    imports: Optional[List[StageWithPath]] = None
    packages: Optional[List[str]] = None
    handler: Optional[str] = None
    external_access_integrations: Optional[List[AccountObjectIdent]] = None
    secrets: Optional[Dict[str, SchemaObjectIdent]] = None


class ProjectionPolicyBlueprint(SchemaObjectBlueprint):
    body: str
    references: List[ProjectionPolicyReference] = []


class ResourceMonitorBlueprint(AbstractBlueprint):
    full_name: AccountObjectIdent
    credit_quota: int
    frequency: str
    triggers: Dict[int, str]


class RowAccessPolicyBlueprint(SchemaObjectBlueprint):
    arguments: List[NameWithType]
    body: str
    references: List[RowAccessPolicyReference] = []


class SchemaBlueprint(AbstractBlueprint):
    full_name: SchemaIdent
    permission_model: Optional[str] = None
    is_sandbox: Optional[bool] = None
    is_transient: Optional[bool] = None
    retention_time: Optional[int] = None
    external_volume: Optional[Ident] = None
    catalog: Optional[Ident] = None
    owner_database_write: List[IdentPattern] = []
    owner_database_read: List[IdentPattern] = []
    owner_schema_write: List[IdentPattern] = []
    owner_schema_read: List[IdentPattern] = []
    owner_integration_usage: List[Ident] = []
    owner_warehouse_usage: List[AccountObjectIdent] = []
    owner_share_read: List[Union[Ident, DatabaseRoleIdent]] = []
    owner_account_grants: List[AccountGrant] = []
    owner_global_roles: List[Ident] = []


class SecretBlueprint(SchemaObjectBlueprint):
    type: str
    api_authentication: Optional[Ident] = None
    oauth_scopes: Optional[List[str]] = None
    oauth_refresh_token: Optional[str] = None
    oauth_refresh_token_expiry_time: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    secret_string: Optional[str] = None


class SequenceBlueprint(SchemaObjectBlueprint):
    start: int
    interval: int
    is_ordered: Optional[bool] = None


class StageBlueprint(SchemaObjectBlueprint):
    url: Optional[str] = None
    storage_integration: Optional[Ident] = None
    encryption: Optional[Dict[str, Union[bool, float, int, str, list]]] = None
    directory: Optional[Dict[str, Union[bool, float, int, str, list]]] = None
    file_format: Optional[SchemaObjectIdent] = None
    copy_options: Optional[Dict[str, Union[bool, float, int, str, list]]] = None
    upload_stage_files: bool = False


class StageFileBlueprint(SchemaObjectBlueprint):
    full_name: StageFileIdent
    local_path: Path
    stage_name: SchemaObjectIdent
    stage_path: Path


class StreamBlueprint(SchemaObjectBlueprint):
    object_type: ObjectType
    object_name: SchemaObjectIdent
    append_only: bool = False
    insert_only: bool = False
    show_initial_rows: bool = None


class TableBlueprint(SchemaObjectBlueprint):
    columns: List[TableColumn]
    cluster_by: Optional[List[str]] = None
    is_transient: bool = False
    retention_time: Optional[int] = None
    change_tracking: bool = False
    search_optimization: Union[bool, List[SearchOptimizationItem]] = False


class TagBlueprint(SchemaObjectBlueprint):
    full_name: SchemaObjectIdent
    references: List[TagReference]


class TaskBlueprint(SchemaObjectBlueprint, DependsOnMixin):
    body: str
    schedule: Optional[str] = None
    after: Optional[List[SchemaObjectIdent]] = None
    finalize: Optional[SchemaObjectIdent] = None
    when: Optional[str] = None
    warehouse: Optional[AccountObjectIdent] = None
    user_task_managed_initial_warehouse_size: Optional[str] = None
    config: Optional[str] = None
    allow_overlapping_execution: Optional[bool] = None
    session_params: Optional[Dict[str, Union[bool, float, int, str]]] = None
    user_task_timeout_ms: Optional[int] = None
    suspend_task_after_num_failures: Optional[int] = None
    error_integration: Optional[Ident] = None
    task_auto_retry_attempts: Optional[int] = None
    user_task_minimum_trigger_interval_in_seconds: Optional[int] = None


class TechnicalRoleBlueprint(AbstractBlueprint):
    full_name: AccountObjectIdent
    grant_patterns: List[GrantPattern] = []
    account_grants: List[AccountGrant] = []


class UniqueKeyBlueprint(SchemaObjectBlueprint):
    full_name: TableConstraintIdent
    table_name: SchemaObjectIdent
    columns: List[Ident]


class UserBlueprint(AbstractBlueprint):
    full_name: AccountObjectIdent
    login_name: str
    display_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    disabled: bool = False
    business_roles: List[AccountObjectIdent] = []
    password: Optional[str] = None
    rsa_public_key: Optional[str] = None
    rsa_public_key_2: Optional[str] = None
    type: Optional[str] = None
    default_warehouse: Optional[AccountObjectIdent] = None
    default_namespace: Optional[Union[DatabaseIdent, SchemaIdent]] = None
    session_params: Dict[str, Union[bool, float, int, str]] = {}


class ViewBlueprint(SchemaObjectBlueprint, DependsOnMixin):
    text: str
    columns: Optional[List[ViewColumn]] = None
    is_secure: bool = False
    change_tracking: bool = False


class WarehouseBlueprint(AbstractBlueprint):
    full_name: AccountObjectIdent
    type: str
    size: str
    auto_suspend: int = 60
    min_cluster_count: int = 1
    max_cluster_count: int = 1
    scaling_policy: str = "STANDARD"
    resource_monitor: Optional[Union[Ident, AccountObjectIdent]] = None
    enable_query_acceleration: bool = False
    query_acceleration_max_scale_factor: int = 8
    warehouse_params: Dict[str, Union[bool, float, int, str]] = {}
    resource_constraint: Optional[str] = None


T_Blueprint = TypeVar("T_Blueprint", bound=AbstractBlueprint)
