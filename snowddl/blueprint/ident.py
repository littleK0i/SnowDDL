from string import ascii_letters, digits
from typing import List

from .data_type import BaseDataType


class Ident:
    allowed_chars = set(ascii_letters + digits + '_')

    def __init__(self, value):
        self.value = self.validate_ident(value)

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"<{self.__class__.__name__}={str(self)}>"

    def __eq__(self, other):
        if not isinstance(other, Ident):
            raise NotImplemented

        return str(self) == str(other)

    def validate_ident(self, value):
        if isinstance(value, Ident):
            value = str(value.value)
        else:
            value = str(value)

        if not value:
            ValueError("Identifier cannot be empty")

        for char in value:
            if char not in self.allowed_chars:
                ValueError(f"Character [{char}] in not allowed in identifier [{value}], only ASCII letters, digits and single underscores are accepted")

        return value.upper()


class IdentWithPrefix(Ident):
    def __init__(self, env_prefix, value):
        self.env_prefix = env_prefix
        self.value = self.validate_ident(value)

    def __str__(self):
        return f"{self.env_prefix}{self.value}"


class ComplexIdentWithPrefix(IdentWithPrefix):
    def __init__(self, env_prefix, *parts):
        self.env_prefix = env_prefix
        self.parts = tuple(self.validate_ident(part) for part in parts)

    def parts_for_format(self):
        parts_for_format = []

        for idx, part in enumerate(self.parts):
            if idx == 0:
                parts_for_format.append(f"{self.env_prefix}{part}")
            else:
                parts_for_format.append(part)

        return parts_for_format

    def __str__(self):
        return '.'.join(self.parts_for_format())


class ComplexIdentWithPrefixAndArgs(ComplexIdentWithPrefix):
    def __init__(self, env_prefix, *parts, data_types: List[BaseDataType]):
        self.env_prefix = env_prefix
        self.parts = tuple(self.validate_ident(part) for part in parts)
        self.data_types = data_types

    def __str__(self):
        return f"{super().__str__()}({','.join(data_type.name for data_type in self.data_types)})"


class ComplexIdentWithPrefixAndPath(ComplexIdentWithPrefix):
    def __init__(self, env_prefix, *parts, path: str):
        self.env_prefix = env_prefix
        self.parts = tuple(self.validate_ident(part) for part in parts)
        self.path = path

    def __str__(self):
        return f"{super().__str__()}({self.path})"
