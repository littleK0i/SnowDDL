from ._parsed_file import ParsedFile
from ._scanner import DirectoryScanner
from .abc_parser import AbstractParser
from .account_params import AccountParameterParser
from .account_policy import AccountPolicyParser
from .aggregation_policy import AggregationPolicyParser
from .alert import AlertParser
from .authentication_policy import AuthenticationPolicyParser
from .business_role import BusinessRoleParser
from .database import DatabaseParser
from .dynamic_table import DynamicTableParser
from .event_table import EventTableParser
from .external_access_integration import ExternalAccessIntegrationParser
from .external_function import ExternalFunctionParser
from .external_table import ExternalTableParser
from .file_format import FileFormatParser
from .function import FunctionParser
from .hybrid_table import HybridTableParser
from .iceberg_table import IcebergTableParser
from .materialized_view import MaterializedViewParser
from .masking_policy import MaskingPolicyParser
from .network_policy import NetworkPolicyParser
from .network_rule import NetworkRuleParser
from .outbound_share import OutboundShareParser
from .permission_model import PermissionModelParser
from .pipe import PipeParser
from .placeholder import PlaceholderParser
from .procedure import ProcedureParser
from .projection_policy import ProjectionPolicyParser
from .resource_monitor import ResourceMonitorParser
from .row_access_policy import RowAccessPolicyParser
from .schema import SchemaParser
from .secret import SecretParser
from .sequence import SequenceParser
from .stage import StageParser
from .stream import StreamParser
from .table import TableParser
from .task import TaskParser
from .technical_role import TechnicalRoleParser
from .user import UserParser
from .view import ViewParser
from .warehouse import WarehouseParser


default_parse_sequence = [
    AccountParameterParser,
    # --
    AggregationPolicyParser,
    AuthenticationPolicyParser,
    MaskingPolicyParser,
    NetworkPolicyParser,
    ProjectionPolicyParser,
    RowAccessPolicyParser,
    ResourceMonitorParser,
    AccountPolicyParser,
    # --
    WarehouseParser,
    DatabaseParser,
    SchemaParser,
    SecretParser,
    NetworkRuleParser,
    ExternalAccessIntegrationParser,
    FileFormatParser,
    StageParser,
    SequenceParser,
    FunctionParser,
    ExternalFunctionParser,
    ProcedureParser,
    TableParser,
    EventTableParser,
    HybridTableParser,
    IcebergTableParser,
    DynamicTableParser,
    ExternalTableParser,
    MaterializedViewParser,
    ViewParser,
    PipeParser,
    StreamParser,
    TaskParser,
    AlertParser,
    # --
    OutboundShareParser,
    TechnicalRoleParser,
    BusinessRoleParser,
    UserParser,
]


singledb_parse_sequence = [
    AggregationPolicyParser,
    MaskingPolicyParser,
    ProjectionPolicyParser,
    RowAccessPolicyParser,
    # --
    DatabaseParser,
    SchemaParser,
    SecretParser,
    NetworkRuleParser,
    FileFormatParser,
    StageParser,
    SequenceParser,
    FunctionParser,
    ExternalFunctionParser,
    ProcedureParser,
    TableParser,
    EventTableParser,
    HybridTableParser,
    IcebergTableParser,
    DynamicTableParser,
    ExternalTableParser,
    MaterializedViewParser,
    ViewParser,
    PipeParser,
    StreamParser,
    TaskParser,
    AlertParser,
]
