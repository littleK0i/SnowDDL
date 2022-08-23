from enum import Enum
from re import compile, IGNORECASE


class BaseDataType(Enum):
    NUMBER = {
        "base_name": "NUMBER",
        "number_of_properties": 2,
    }

    FLOAT = {
        "base_name": "FLOAT",
        "number_of_properties": 0,
    }

    BINARY = {
        "base_name": "BINARY",
        "number_of_properties": 1,
    }

    BOOLEAN = {
        "base_name": "BOOLEAN",
        "number_of_properties": 0,
    }

    VARCHAR = {
        "base_name": "VARCHAR",
        "number_of_properties": 1,
    }

    DATE = {
        "base_name": "DATE",
        "number_of_properties": 0,
    }

    TIME = {
        "base_name": "TIME",
        "number_of_properties": 1,
    }

    TIMESTAMP_LTZ = {
        "base_name": "TIMESTAMP_LTZ",
        "number_of_properties": 1,
    }

    TIMESTAMP_NTZ = {
        "base_name": "TIMESTAMP_NTZ",
        "number_of_properties": 1,
    }

    TIMESTAMP_TZ = {
        "base_name": "TIMESTAMP_TZ",
        "number_of_properties": 1,
    }

    VARIANT = {
        "base_name": "VARIANT",
        "number_of_properties": 0,
    }

    OBJECT = {
        "base_name": "OBJECT",
        "number_of_properties": 0,
    }

    ARRAY = {
        "base_name": "ARRAY",
        "number_of_properties": 0,
    }

    GEOGRAPHY = {
        "base_name": "GEOGRAPHY",
        "number_of_properties": 0,
    }

    GEOMETRY = {
        "base_name": "GEOMETRY",
        "number_of_properties": 0,
    }

    @property
    def number_of_properties(self) -> int:
        return self.value.get('number_of_properties', 0)

    def __repr__(self):
        return f"<{self.__class__.__name__}.{self.name}>"


class DataType:
    data_type_re = compile(r'^(?P<base_type>[a-z0-9_]+)(\((?P<val1>\d+)(,(?P<val2>\d+))?\))?$', IGNORECASE)

    def __init__(self, data_type_str):
        m = self.data_type_re.match(data_type_str)

        if not m:
            raise ValueError(f"Could not parse data type string [{data_type_str}]")

        try:
            self.base_type = BaseDataType[str(m['base_type']).upper()]
        except KeyError:
            raise ValueError(f"Invalid base data type [{m['base_type']}] in type string [{data_type_str}]")

        self.val1 = int(m['val1']) if self.base_type.number_of_properties >= 1 else None
        self.val2 = int(m['val2']) if self.base_type.number_of_properties >= 2 else None

    def __str__(self):
        if self.base_type.number_of_properties >= 2:
            return f"{self.base_type.name}({self.val1},{self.val2})"
        elif self.base_type.number_of_properties >= 1:
            return f"{self.base_type.name}({self.val1})"

        return self.base_type.name

    def __repr__(self):
        return f"<{self.__class__.__name__}.{str(self)}>"

    def __eq__(self, other):
        if not isinstance(other, DataType):
            raise NotImplemented

        return str(self) == str(other)
