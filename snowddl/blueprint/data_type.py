from enum import Enum
from re import compile, IGNORECASE
from typing import List


class BaseDataType(Enum):
    NUMBER = {
        "base_name": "NUMBER",
        "number_of_properties": 2,
        "default_properties": [38, 0],
    }

    FILE = {
        "base_name": "FILE",
        "number_of_properties": 0,
        "default_properties": [],
    }

    FLOAT = {
        "base_name": "FLOAT",
        "number_of_properties": 0,
        "default_properties": [],
    }

    BINARY = {
        "base_name": "BINARY",
        "number_of_properties": 1,
        "default_properties": [8_388_608],
    }

    BOOLEAN = {
        "base_name": "BOOLEAN",
        "number_of_properties": 0,
        "default_properties": [],
    }

    VARCHAR = {
        "base_name": "VARCHAR",
        "number_of_properties": 1,
        "default_properties": [16_777_216],
    }

    DATE = {
        "base_name": "DATE",
        "number_of_properties": 0,
        "default_properties": [],
    }

    TIME = {
        "base_name": "TIME",
        "number_of_properties": 1,
        "default_properties": [9],
    }

    TIMESTAMP_LTZ = {
        "base_name": "TIMESTAMP_LTZ",
        "number_of_properties": 1,
        "default_properties": [9],
    }

    TIMESTAMP_NTZ = {
        "base_name": "TIMESTAMP_NTZ",
        "number_of_properties": 1,
        "default_properties": [9],
    }

    TIMESTAMP_TZ = {
        "base_name": "TIMESTAMP_TZ",
        "number_of_properties": 1,
        "default_properties": [9],
    }

    VARIANT = {
        "base_name": "VARIANT",
        "number_of_properties": 0,
        "default_properties": [],
    }

    OBJECT = {
        "base_name": "OBJECT",
        "number_of_properties": 0,
        "default_properties": [],
    }

    ARRAY = {
        "base_name": "ARRAY",
        "number_of_properties": 0,
        "default_properties": [],
    }

    GEOGRAPHY = {
        "base_name": "GEOGRAPHY",
        "number_of_properties": 0,
        "default_properties": [],
    }

    GEOMETRY = {
        "base_name": "GEOMETRY",
        "number_of_properties": 0,
        "default_properties": [],
    }

    VECTOR = {
        "base_name": "VECTOR",
        "number_of_properties": 2,
        "default_properties": [],
    }

    @property
    def number_of_properties(self) -> int:
        return self.value["number_of_properties"]

    @property
    def default_properties(self) -> List[int]:
        return self.value["default_properties"]

    def __repr__(self):
        return f"<{self.__class__.__name__}.{self.name}>"


class DataType:
    data_type_re = compile(
        r"^(?P<base_type>[a-z0-9_]+)(\((?P<val1>\d+)(,(?P<val2>\d+))?\)|\((?P<val1_vector>int|float),\s?(?P<val2_vector>\d+)\))?$",
        IGNORECASE,
    )

    def __init__(self, data_type_str):
        m = self.data_type_re.match(data_type_str)

        if not m:
            raise ValueError(f"Could not parse data type string [{data_type_str}]")

        try:
            self.base_type = BaseDataType[str(m["base_type"]).upper()]
        except KeyError:
            raise ValueError(f"Invalid base data type [{m['base_type']}] in type string [{data_type_str}]")

        if self.base_type == BaseDataType.VECTOR:
            self.val1 = str(m["val1_vector"]).upper()
            self.val2 = int(m["val2_vector"])
        else:
            self.val1 = int(m["val1"]) if self.base_type.number_of_properties >= 1 else None
            self.val2 = int(m["val2"]) if self.base_type.number_of_properties >= 2 else None

    @staticmethod
    def from_base_type(base_type: BaseDataType):
        if base_type.default_properties:
            return DataType(f"{base_type.name}({','.join(str(p) for p in base_type.default_properties)})")

        return DataType(base_type.name)

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
            raise NotImplementedError

        return str(self) == str(other)
