from enum import Enum


class ObjectType(Enum):
    # Technical object type, used for GRANTs only
    # There is no blueprint
    ACCOUNT = {
        "singular": "ACCOUNT",
        "plural": "ACCOUNTS",
    }

    ACCOUNT_PARAMETER = {
        "singular": "ACCOUNT PARAMETER",
        "plural": "ACCOUNT PARAMETERS",
        "blueprint_cls": "AccountParameterBlueprint",
    }

    AGGREGATION_POLICY = {
        "singular": "AGGREGATION POLICY",
        "plural": "AGGREGATION POLICIES",
        "blueprint_cls": "AggregationPolicyBlueprint",
    }

    ALERT = {
        "singular": "ALERT",
        "plural": "ALERTS",
        "is_future_grant_supported": True,
        "blueprint_cls": "AlertBlueprint",
    }

    CLONE_TABLE = {
        "singular": "CLONE TABLE",
        "plural": "CLONE TABLES",
        "blueprint_cls": "TableBlueprint",
    }

    DATABASE = {
        "singular": "DATABASE",
        "plural": "DATABASES",
        "blueprint_cls": "DatabaseBlueprint",
    }

    # Technical object type, used for GRANTs only
    # There is no blueprint
    DATABASE_ROLE = {
        "singular": "DATABASE ROLE",
        "plural": "DATABASE ROLES",
    }

    DYNAMIC_TABLE = {
        "singular": "DYNAMIC TABLE",
        "plural": "DYNAMIC TABLES",
        "singular_for_ref": "TABLE",
        "is_future_grant_supported": True,
        "blueprint_cls": "DynamicTableBlueprint",
    }

    EVENT_TABLE = {
        "singular": "EVENT TABLE",
        "plural": "EVENT TABLES",
        "singular_for_ref": "TABLE",
        "is_future_grant_supported": True,
        "blueprint_cls": "EventTableBlueprint",
    }

    EXTERNAL_ACCESS_INTEGRATION = {
        "singular": "EXTERNAL ACCESS INTEGRATION",
        "plural": "EXTERNAL ACCESS INTEGRATIONS",
        "singular_for_ref": "INTEGRATION",
        "singular_for_grant": "INTEGRATION",
        "blueprint_cls": "ExternalAccessIntegrationBlueprint",
    }

    EXTERNAL_FUNCTION = {
        "singular": "EXTERNAL FUNCTION",
        "plural": "EXTERNAL FUNCTIONS",
        "is_future_grant_supported": True,
        "blueprint_cls": "ExternalFunctionBlueprint",
    }

    EXTERNAL_TABLE = {
        "singular": "EXTERNAL TABLE",
        "plural": "EXTERNAL TABLES",
        "singular_for_ref": "TABLE",
        "is_future_grant_supported": True,
        "blueprint_cls": "ExternalTableBlueprint",
    }

    FILE_FORMAT = {
        "singular": "FILE FORMAT",
        "plural": "FILE FORMATS",
        "is_future_grant_supported": True,
        "blueprint_cls": "FileFormatBlueprint",
    }

    FUNCTION = {
        "singular": "FUNCTION",
        "plural": "FUNCTIONS",
        "is_future_grant_supported": True,
        "is_overloading_supported": True,
        "blueprint_cls": "FunctionBlueprint",
    }

    HYBRID_TABLE = {
        "singular": "HYBRID TABLE",
        "plural": "HYBRID TABLES",
        "singular_for_ref": "TABLE",
        "is_future_grant_supported": True,
        "blueprint_cls": "HybridTableBlueprint",
    }

    # Technical object type, used for GRANTs only
    # There is no blueprint
    INTEGRATION = {
        "singular": "INTEGRATION",
        "plural": "INTEGRATIONS",
    }

    MASKING_POLICY = {
        "singular": "MASKING POLICY",
        "plural": "MASKING POLICIES",
        "blueprint_cls": "MaskingPolicyBlueprint",
    }

    MATERIALIZED_VIEW = {
        "singular": "MATERIALIZED VIEW",
        "plural": "MATERIALIZED VIEWS",
        "singular_for_ref": "VIEW",
        "is_future_grant_supported": True,
        "blueprint_cls": "MaterializedViewBlueprint",
    }

    NETWORK_POLICY = {
        "singular": "NETWORK POLICY",
        "plural": "NETWORK POLICIES",
        "blueprint_cls": "NetworkPolicyBlueprint",
    }

    NETWORK_RULE = {
        "singular": "NETWORK RULE",
        "plural": "NETWORK RULES",
        "is_future_grant_supported": True,
        "blueprint_cls": "NetworkRuleBlueprint",
    }

    NOTEBOOK = {
        "singular": "NOTEBOOK",
        "plural": "NOTEBOOKS",
    }

    PIPE = {
        "singular": "PIPE",
        "plural": "PIPES",
        "is_future_grant_supported": True,
        "blueprint_cls": "PipeBlueprint",
    }

    PROCEDURE = {
        "singular": "PROCEDURE",
        "plural": "PROCEDURES",
        "is_future_grant_supported": True,
        "is_overloading_supported": True,
        "blueprint_cls": "ProcedureBlueprint",
    }

    PROJECTION_POLICY = {
        "singular": "PROJECTION POLICY",
        "plural": "PROJECTION POLICIES",
        "blueprint_cls": "ProjectionPolicyBlueprint",
    }

    RESOURCE_MONITOR = {
        "singular": "RESOURCE MONITOR",
        "plural": "RESOURCE MONITORS",
        "blueprint_cls": "ResourceMonitorBlueprint",
    }

    ROLE = {
        "singular": "ROLE",
        "plural": "ROLES",
        "blueprint_cls": "RoleBlueprint",
    }

    ROW_ACCESS_POLICY = {
        "singular": "ROW ACCESS POLICY",
        "plural": "ROW ACCESS POLICIES",
        "blueprint_cls": "RowAccessPolicyBlueprint",
    }

    SCHEMA = {
        "singular": "SCHEMA",
        "plural": "SCHEMAS",
        "is_future_grant_supported": True,
        "blueprint_cls": "SchemaBlueprint",
    }

    SECRET = {
        "singular": "SECRET",
        "plural": "SECRETS",
        "is_future_grant_supported": True,
        "blueprint_cls": "SecretBlueprint",
    }

    SEQUENCE = {
        "singular": "SEQUENCE",
        "plural": "SEQUENCES",
        "is_future_grant_supported": True,
        "blueprint_cls": "SequenceBlueprint",
    }

    SHARE = {
        "singluar": "SHARE",
        "plural": "SHARES",
        "blueprint_cls": "OutboundShareBlueprint",
    }

    STAGE = {
        "singular": "STAGE",
        "plural": "STAGES",
        "is_future_grant_supported": True,
        "blueprint_cls": "StageBlueprint",
    }

    STAGE_FILE = {
        "singular": "STAGE FILE",
        "plural": "STAGE FILES",
        "blueprint_cls": "StageFileBlueprint",
    }

    STREAM = {
        "singular": "STREAM",
        "plural": "STREAMS",
        "is_future_grant_supported": True,
        "blueprint_cls": "StreamBlueprint",
    }

    TABLE = {
        "singular": "TABLE",
        "plural": "TABLES",
        "is_future_grant_supported": True,
        "blueprint_cls": "TableBlueprint",
    }

    TAG = {
        "singular": "TAG",
        "plural": "TAGS",
        "is_future_grant_supported": True,
        "blueprint_cls": "TagBlueprint",
    }

    TASK = {
        "singular": "TASK",
        "plural": "TASKS",
        "is_future_grant_supported": True,
        "blueprint_cls": "TaskBlueprint",
    }

    VIEW = {
        "singular": "VIEW",
        "plural": "VIEWS",
        "is_future_grant_supported": True,
        "blueprint_cls": "ViewBlueprint",
    }

    USER = {
        "singular": "USER",
        "plural": "USERS",
        "blueprint_cls": "UserBlueprint",
    }

    WAREHOUSE = {
        "singular": "WAREHOUSE",
        "plural": "WAREHOUSES",
        "blueprint_cls": "WarehouseBlueprint",
    }

    # Constraints
    PRIMARY_KEY = {
        "singular": "PRIMARY KEY",
        "plural": "PRIMARY KEYS",
        "blueprint_cls": "PrimaryKeyBlueprint",
    }

    UNIQUE_KEY = {
        "singular": "UNIQUE KEY",
        "plural": "UNIQUE KEYS",
        "blueprint_cls": "UniqueKeyBlueprint",
    }

    FOREIGN_KEY = {
        "singular": "FOREIGN KEY",
        "plural": "FOREIGN KEYS",
        "blueprint_cls": "ForeignKeyBlueprint",
    }

    @property
    def singular(self):
        return self.value.get("singular")

    @property
    def plural(self):
        return self.value.get("plural")

    @property
    def singular_for_grant(self):
        return self.value.get("singular_for_grant", self.value.get("singular"))

    @property
    def singular_for_ref(self):
        return self.value.get("singular_for_ref", self.value.get("singular"))

    @property
    def blueprint_cls(self):
        # This import prevents cicrular dependency between blueprints and object types
        from . import blueprint

        return getattr(blueprint, self.value.get("blueprint_cls"))

    @property
    def is_future_grant_supported(self) -> bool:
        return self.value.get("is_future_grant_supported", False)

    @property
    def is_overloading_supported(self) -> bool:
        return self.value.get("is_overloading_supported", False)

    def __repr__(self):
        return f"<{self.__class__.__name__}.{super().name}>"
