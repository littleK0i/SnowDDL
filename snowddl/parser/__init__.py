from ._parsed_file import ParsedFile
from .account_params import AccountParameterParser
from .business_role import BusinessRoleParser
from .database import DatabaseParser
from .external_function import ExternalFunctionParser
from .external_table import ExternalTableParser
from .file_format import FileFormatParser
from .function import FunctionParser
from .materialized_view import MaterializedViewParser
from .masking_policy import MaskingPolicyParser
from .network_policy import NetworkPolicyParser
from .pipe import PipeParser
from .placeholder import PlaceholderParser
from .procedure import ProcedureParser
from .resource_monitor import ResourceMonitorParser
from .row_access_policy import RowAccessPolicyParser
from .schema import SchemaParser
from .sequence import SequenceParser
from .stage import StageParser
from .stream import StreamParser
from .table import TableParser
from .task import TaskParser
from .tech_role import TechRoleParser
from .user import UserParser
from .view import ViewParser
from .warehouse import WarehouseParser


default_parser_sequence = [
    AccountParameterParser,
    NetworkPolicyParser,
    ResourceMonitorParser,
    WarehouseParser,
    DatabaseParser,
    SchemaParser,
    FileFormatParser,
    StageParser,
    SequenceParser,
    FunctionParser,
    ExternalFunctionParser,
    ProcedureParser,
    TableParser,
    ExternalTableParser,
    StreamParser,
    MaterializedViewParser,
    ViewParser,
    PipeParser,
    TaskParser,
    MaskingPolicyParser,
    RowAccessPolicyParser,
    TechRoleParser,
    BusinessRoleParser,
    UserParser,
]
