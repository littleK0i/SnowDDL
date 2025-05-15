from .abc_resolver import AbstractResolver, ResolveResult
from .abc_role_resolver import AbstractRoleResolver
from .abc_schema_object_resolver import AbstractSchemaObjectResolver
from .account_params import AccountParameterResolver
from .aggregation_policy import AggregationPolicyResolver
from .authentication_policy import AuthenticationPolicyResolver
from .alert import AlertResolver
from .business_role import BusinessRoleResolver
from .clone_table import CloneTableResolver
from .database import DatabaseResolver
from .database_owner_role import DatabaseOwnerRoleResolver
from .database_read_role import DatabaseReadRoleResolver
from .database_role import DatabaseRoleResolver
from .database_write_role import DatabaseWriteRoleResolver
from .dynamic_table import DynamicTableResolver
from .event_table import EventTableResolver
from .external_access_integration import ExternalAccessIntegrationResolver
from .external_function import ExternalFunctionResolver
from .external_table import ExternalTableResolver
from .file_format import FileFormatResolver
from .foreign_key import ForeignKeyResolver
from .function import FunctionResolver
from .hybrid_table import HybridTableResolver
from .iceberg_table import IcebergTableResolver
from .masking_policy import MaskingPolicyResolver
from .materialized_view import MaterializedViewResolver
from .network_policy import NetworkPolicyResolver
from .network_rule import NetworkRuleResolver
from .outbound_share import OutboundShareResolver
from .pipe import PipeResolver
from .primary_key import PrimaryKeyResolver
from .procedure import ProcedureResolver
from .projection_policy import ProjectionPolicyResolver
from .resource_monitor import ResourceMonitorResolver
from .row_access_policy import RowAccessPolicyResolver
from .sequence import SequenceResolver
from .share_access_role import ShareAccessRoleResolver
from .schema import SchemaResolver
from .schema_owner_role import SchemaOwnerRoleResolver
from .schema_read_role import SchemaReadRoleResolver
from .schema_write_role import SchemaWriteRoleResolver
from .secret import SecretResolver
from .semantic_view import SemanticViewResolver
from .stage import StageResolver
from .stage_file import StageFileResolver
from .stream import StreamResolver
from .table import TableResolver
from .task import TaskResolver
from .technical_role import TechnicalRoleResolver
from .view import ViewResolver
from .unique_key import UniqueKeyResolver
from .user import UserResolver
from .user_role import UserRoleResolver
from .warehouse import WarehouseResolver
from .warehouse_monitor_role import WarehouseMonitorRoleResolver
from .warehouse_usage_role import WarehouseUsageRoleResolver


default_resolve_sequence = [
    AccountParameterResolver,
    ResourceMonitorResolver,
    WarehouseResolver,
    WarehouseMonitorRoleResolver,
    WarehouseUsageRoleResolver,
    DatabaseResolver,
    SchemaResolver,
    ShareAccessRoleResolver,
    DatabaseReadRoleResolver,
    DatabaseWriteRoleResolver,
    SchemaReadRoleResolver,
    SchemaWriteRoleResolver,
    DatabaseOwnerRoleResolver,
    SchemaOwnerRoleResolver,
    SecretResolver,
    NetworkRuleResolver,
    ExternalAccessIntegrationResolver,
    FileFormatResolver,
    StageResolver,
    StageFileResolver,
    SequenceResolver,
    FunctionResolver,
    ExternalFunctionResolver,
    ProcedureResolver,
    CloneTableResolver,
    TableResolver,
    EventTableResolver,
    HybridTableResolver,
    IcebergTableResolver,
    DynamicTableResolver,
    ExternalTableResolver,
    PrimaryKeyResolver,
    UniqueKeyResolver,
    ForeignKeyResolver,
    MaterializedViewResolver,
    ViewResolver,
    SemanticViewResolver,
    PipeResolver,
    StreamResolver,
    TaskResolver,
    AlertResolver,
    # --
    DatabaseRoleResolver,
    OutboundShareResolver,
    TechnicalRoleResolver,
    BusinessRoleResolver,
    UserRoleResolver,
    UserResolver,
    # --
    AggregationPolicyResolver,
    AuthenticationPolicyResolver,
    MaskingPolicyResolver,
    NetworkPolicyResolver,
    ProjectionPolicyResolver,
    RowAccessPolicyResolver,
]


default_destroy_sequence = [
    AccountParameterResolver,
    ResourceMonitorResolver,
    WarehouseResolver,
    WarehouseMonitorRoleResolver,
    WarehouseUsageRoleResolver,
    # --
    NetworkPolicyResolver,
    AuthenticationPolicyResolver,
    ExternalAccessIntegrationResolver,
    OutboundShareResolver,
    # --
    DatabaseResolver,
    SchemaResolver,
    ShareAccessRoleResolver,
    DatabaseReadRoleResolver,
    DatabaseWriteRoleResolver,
    SchemaReadRoleResolver,
    SchemaWriteRoleResolver,
    DatabaseOwnerRoleResolver,
    SchemaOwnerRoleResolver,
    # --
    DatabaseRoleResolver,
    TechnicalRoleResolver,
    BusinessRoleResolver,
    UserRoleResolver,
    UserResolver,
]


singledb_resolve_sequence = [
    SchemaResolver,
    SecretResolver,
    NetworkRuleResolver,
    FileFormatResolver,
    StageResolver,
    StageFileResolver,
    SequenceResolver,
    FunctionResolver,
    ExternalFunctionResolver,
    ProcedureResolver,
    CloneTableResolver,
    TableResolver,
    EventTableResolver,
    HybridTableResolver,
    IcebergTableResolver,
    DynamicTableResolver,
    ExternalTableResolver,
    PrimaryKeyResolver,
    UniqueKeyResolver,
    ForeignKeyResolver,
    MaterializedViewResolver,
    ViewResolver,
    SemanticViewResolver,
    PipeResolver,
    StreamResolver,
    TaskResolver,
    AlertResolver,
    # --
    DatabaseRoleResolver,
    AggregationPolicyResolver,
    MaskingPolicyResolver,
    ProjectionPolicyResolver,
    RowAccessPolicyResolver,
]


singledb_destroy_sequence = [
    SchemaResolver,
    DatabaseRoleResolver,
]
