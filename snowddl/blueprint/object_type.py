from enum import Enum


class ObjectType(Enum):
    ACCOUNT_PARAMETER = {
        "singular": "ACCOUNT PARAMETER",
        "plural": "ACCOUNT PARAMETERS",
    }

    DATABASE = {
        "singular": "DATABASE",
        "plural": "DATABASES",
    }

    EXTERNAL_FUNCTION = {
        "singular": "EXTERNAL FUNCTION",
        "plural": "EXTERNAL FUNCTIONS",
        "is_future_grant_supported": True,
    }

    EXTERNAL_TABLE = {
        "singular": "EXTERNAL TABLE",
        "plural": "EXTERNAL TABLES",
        "simplified": "TABLE",
        "is_future_grant_supported": True,
    }

    FILE_FORMAT = {
        "singular": "FILE FORMAT",
        "plural": "FILE FORMATS",
        "is_future_grant_supported": True,
    }

    FUNCTION = {
        "singular": "FUNCTION",
        "plural": "FUNCTIONS",
        "is_future_grant_supported": True,
    }

    MASKING_POLICY = {
        "singular": "MASKING POLICY",
        "plural": "MASKING POLICIES",
    }

    MATERIALIZED_VIEW = {
        "singular": "MATERIALIZED VIEW",
        "plural": "MATERIALIZED VIEWS",
        "simplified": "VIEW",
        "is_future_grant_supported": True,
    }

    NETWORK_POLICY = {
        "singular": "NETWORK POLICY",
        "plural": "NETWORK POLICIES",
    }

    PIPE = {
        "singular": "PIPE",
        "plural": "PIPES",
        "is_future_grant_supported": True,
    }

    PROCEDURE = {
        "singular": "PROCEDURE",
        "plural": "PROCEDURES",
        "is_future_grant_supported": True,
    }

    RESOURCE_MONITOR = {
        "singular": "RESOURCE MONITOR",
        "plural": "RESOURCE MONITORS",
    }

    ROLE = {
        "singular": "ROLE",
        "plural": "ROLES",
    }

    ROW_ACCESS_POLICY = {
        "singular": "ROW ACCESS POLICY",
        "plural": "ROW ACCESS POLICIES",
    }

    SEQUENCE = {
        "singular": "SEQUENCE",
        "plural": "SEQUENCES",
        "is_future_grant_supported": True,
    }

    SCHEMA = {
        "singular": "SCHEMA",
        "plural": "SCHEMAS",
        "is_future_grant_supported": True,
    }

    STAGE = {
        "singular": "STAGE",
        "plural": "STAGES",
        "is_future_grant_supported": True,
    }

    STAGE_FILE = {
        "singular": "STAGE FILE",
        "plural": "STAGE FILES",
    }

    STREAM = {
        "singular": "STREAM",
        "plural": "STREAMS",
        "is_future_grant_supported": True,
    }

    TABLE = {
        "singular": "TABLE",
        "plural": "TABLES",
        "is_future_grant_supported": True,
    }

    TAG = {
        "singular": "TAG",
        "plural": "TAGS",
        "is_future_grant_supported": True,
    }

    TASK = {
        "singular": "TASK",
        "plural": "TASKS",
        "is_future_grant_supported": True,
    }

    VIEW = {
        "singular": "VIEW",
        "plural": "VIEWS",
        "is_future_grant_supported": True,
    }

    USER = {
        "singular": "USER",
        "plural": "USERS",
    }

    WAREHOUSE = {
        "singular": "WAREHOUSE",
        "plural": "WAREHOUSES",
    }

    # Constraints
    PRIMARY_KEY = {
        "singular": "PRIMARY KEY",
        "plural": "PRIMARY KEYS",
    }

    UNIQUE_KEY = {
        "singular": "UNIQUE KEY",
        "plural": "UNIQUE KEYS",
    }

    FOREIGN_KEY = {
        "singular": "FOREIGN KEY",
        "plural": "FOREIGN KEYS",
    }

    @property
    def singular(self):
        return self.value.get('singular')

    @property
    def plural(self):
        return self.value.get('plural')

    @property
    def simplified(self):
        return self.value.get('simplified', self.value.get('singular'))

    @property
    def is_future_grant_supported(self) -> bool:
        return self.value.get('is_future_grant_supported', False)

    def __repr__(self):
        return f"<{self.__class__.__name__}.{super().name}>"
