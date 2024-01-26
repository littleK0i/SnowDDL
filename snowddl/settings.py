from typing import Optional, List

from snowddl.blueprint import DatabaseIdent, ObjectType, Ident
from snowddl.model import BaseModelWithConfig


class SnowDDLSettings(BaseModelWithConfig):
    env_admin_role: Optional[Ident] = None
    execute_safe_ddl: bool = False
    execute_unsafe_ddl: bool = False
    execute_replace_table: bool = False
    execute_masking_policy: bool = False
    execute_row_access_policy: bool = False
    execute_account_params: bool = False
    execute_network_policy: bool = False
    execute_resource_monitor: bool = False
    execute_inbound_share: bool = False
    execute_outbound_share: bool = False
    refresh_user_passwords: bool = False
    refresh_future_grants: bool = False
    refresh_stage_encryption: bool = False
    refresh_secrets: bool = False
    clone_table: bool = False
    exclude_object_types: List[ObjectType] = []
    include_object_types: List[ObjectType] = []
    include_databases: List[DatabaseIdent] = []
    ignore_ownership: bool = False
    add_include_files: bool = False
    max_workers: int = 8
