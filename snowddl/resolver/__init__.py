from .abc_resolver import AbstractResolver, ResolveResult
from .abc_role_resolver import AbstractRoleResolver
from .abc_schema_object_resolver import AbstractSchemaObjectResolver
from .account_params import AccountParameterResolver
from .business_role import BusinessRoleResolver
from .database import DatabaseResolver
from .external_function import ExternalFunctionResolver
from .external_table import ExternalTableResolver
from .file_format import FileFormatResolver
from .foreign_key import ForeignKeyResolver
from .function import FunctionResolver
from .masking_policy import MaskingPolicyResolver
from .materialized_view import MaterializedViewResolver
from .network_policy import NetworkPolicyResolver
from .pipe import PipeResolver
from .primary_key import PrimaryKeyResolver
from .procedure import ProcedureResolver
from .resource_monitor import ResourceMonitorResolver
from .row_access_policy import RowAccessPolicyResolver
from .sequence import SequenceResolver
from .schema import SchemaResolver
from .schema_role import SchemaRoleResolver
from .stage import StageResolver
from .stage_file import StageFileResolver
from .stream import StreamResolver
from .table import TableResolver
from .task import TaskResolver
from .tech_role import TechRoleResolver
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
    SchemaRoleResolver,
    FileFormatResolver,
    StageResolver,
    StageFileResolver,
    SequenceResolver,
    FunctionResolver,
    ExternalFunctionResolver,
    ProcedureResolver,
    TableResolver,
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
    TechRoleResolver,
    BusinessRoleResolver,
    UserRoleResolver,
    UserResolver,
]
