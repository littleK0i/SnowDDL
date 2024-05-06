from .abc_resolver import AbstractResolver, ResolveResult
from .abc_role_resolver import AbstractRoleResolver
from .abc_schema_object_resolver import AbstractSchemaObjectResolver
from .account_params import AccountParameterResolver
from .alert import AlertResolver
from .business_role import BusinessRoleResolver
from .clone_table import CloneTableResolver
from .database import DatabaseResolver
from .database_role import DatabaseRoleResolver
from .dynamic_table import DynamicTableResolver
from .event_table import EventTableResolver
from .external_access_integration import ExternalAccessIntegrationResolver
from .external_function import ExternalFunctionResolver
from .external_table import ExternalTableResolver
from .file_format import FileFormatResolver
from .foreign_key import ForeignKeyResolver
from .function import FunctionResolver
from .hybrid_table import HybridTableResolver
from .inbound_share import InboundShareResolver
from .inbound_share_role import InboundShareRoleResolver
from .masking_policy import MaskingPolicyResolver
from .materialized_view import MaterializedViewResolver
from .network_policy import NetworkPolicyResolver
from .network_rule import NetworkRuleResolver
from .outbound_share import OutboundShareResolver
from .pipe import PipeResolver
from .primary_key import PrimaryKeyResolver
from .procedure import ProcedureResolver
from .resource_monitor import ResourceMonitorResolver
from .row_access_policy import RowAccessPolicyResolver
from .sequence import SequenceResolver
from .schema import SchemaResolver
from .schema_role import SchemaRoleResolver
from .secret import SecretResolver
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
from .warehouse_role import WarehouseRoleResolver


default_resolver_sequence = [
    AccountParameterResolver,
    NetworkPolicyResolver,
    ResourceMonitorResolver,
    WarehouseResolver,
    WarehouseRoleResolver,
    DatabaseResolver,
    SchemaResolver,
    DatabaseRoleResolver,
    SchemaRoleResolver,
    # InboundShareResolver,
    # InboundShareRoleResolver,
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
    DynamicTableResolver,
    ExternalTableResolver,
    PrimaryKeyResolver,
    UniqueKeyResolver,
    ForeignKeyResolver,
    StreamResolver,
    MaterializedViewResolver,
    ViewResolver,
    PipeResolver,
    TaskResolver,
    MaskingPolicyResolver,
    RowAccessPolicyResolver,
    OutboundShareResolver,
    TechnicalRoleResolver,
    BusinessRoleResolver,
    UserRoleResolver,
    UserResolver,
    AlertResolver,
]


singledb_resolver_sequence = [
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
    DynamicTableResolver,
    ExternalTableResolver,
    PrimaryKeyResolver,
    UniqueKeyResolver,
    ForeignKeyResolver,
    StreamResolver,
    MaterializedViewResolver,
    ViewResolver,
    PipeResolver,
    TaskResolver,
    MaskingPolicyResolver,
    RowAccessPolicyResolver,
    AlertResolver,
]
