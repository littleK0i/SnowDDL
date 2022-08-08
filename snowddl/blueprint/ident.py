from abc import ABC, abstractmethod
from string import ascii_letters, digits
from typing import List, Optional, Tuple

from .data_type import BaseDataType


class AbstractIdent(ABC):
    allowed_chars = set(ascii_letters + digits + '_$')

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def parts_for_format(self) -> Tuple[List[str], Optional[List[str]]]:
        pass

    def __str__(self):
        core_parts, argument_parts = self.parts_for_format()

        if argument_parts is not None:
            return f"{'.'.join(core_parts)}({','.join(argument_parts)})"

        return '.'.join(core_parts)

    def __repr__(self):
        return f"<{self.__class__.__name__}={str(self)}>"

    def __eq__(self, other):
        if not isinstance(other, AbstractIdent):
            raise NotImplementedError

        return str(self) == str(other)

    def _validate_part(self, val):
        val = str(val)

        if not val:
            raise ValueError("Identifier cannot be empty")

        for char in val:
            if char not in self.allowed_chars:
                raise ValueError(f"Character [{char}] in not allowed in identifier [{val}], only ASCII letters, digits and single underscores are accepted")

        return val.upper()


class AbstractIdentWithPrefix(AbstractIdent, ABC):
    def __init__(self, env_prefix):
        self.env_prefix = self._validate_env_prefix(env_prefix)

    def _validate_env_prefix(self, val):
        val = str(val)

        for char in val:
            if char not in self.allowed_chars:
                raise ValueError(f"Character [{char}] in not allowed in env prefix [{val}], only ASCII letters, digits and single underscores are accepted")

        if val and not val.endswith('__'):
            raise ValueError(f"Env prefix [{val}] in identifier must end with [__] double underscore")

        return val.upper()


class Ident(AbstractIdent):
    def __init__(self, name):
        self.name = self._validate_part(name)

    def parts_for_format(self):
        return [self.name], None


class AccountIdent(AbstractIdent):
    def __init__(self, organization, account):
        self.organization = self._validate_part(organization)
        self.account = self._validate_part(account)

    def parts_for_format(self):
        return [self.organization, self.account], None


class AccountObjectIdent(AbstractIdentWithPrefix):
    def __init__(self, env_prefix, name):
        super().__init__(env_prefix)

        self.name = self._validate_part(name)

    def parts_for_format(self):
        return [f"{self.env_prefix}{self.name}"], None


class DatabaseIdent(AbstractIdentWithPrefix):
    def __init__(self, env_prefix, database):
        super().__init__(env_prefix)

        self.database = self._validate_part(database)

    def parts_for_format(self):
        return [f"{self.env_prefix}{self.database}"], None


class InboundShareIdent(AbstractIdent):
    def __init__(self, organization, account, share):
        self.organization = self._validate_part(organization)
        self.account = self._validate_part(account)
        self.share = self._validate_part(share)

    def parts_for_format(self):
        return [self.organization, self.account, self.share], None


class OutboundShareIdent(AbstractIdentWithPrefix):
    def __init__(self, env_prefix, share):
        super().__init__(env_prefix)

        self.share = self._validate_part(share)

    def parts_for_format(self):
        return [f"{self.env_prefix}{self.share}"], None


class SchemaIdent(AbstractIdentWithPrefix):
    def __init__(self, env_prefix, database, schema):
        super().__init__(env_prefix)

        self.database = self._validate_part(database)
        self.schema = self._validate_part(schema)

    def parts_for_format(self):
        return [f"{self.env_prefix}{self.database}", self.schema], None

    @property
    def database_full_name(self):
        return DatabaseIdent(self.env_prefix, self.database)


class SchemaObjectIdent(AbstractIdentWithPrefix):
    def __init__(self, env_prefix, database, schema, name):
        super().__init__(env_prefix)

        self.database = self._validate_part(database)
        self.schema = self._validate_part(schema)
        self.name = self._validate_part(name)

    def parts_for_format(self):
        return [f"{self.env_prefix}{self.database}", self.schema, self.name], None

    @property
    def database_full_name(self):
        return DatabaseIdent(self.env_prefix, self.database)


class SchemaObjectIdentWithArgs(SchemaObjectIdent):
    def __init__(self, env_prefix, database, schema, name, data_types: List[BaseDataType]):
        super().__init__(env_prefix, database, schema, name)

        self.data_types = data_types

    def parts_for_format(self):
        return [f"{self.env_prefix}{self.database}", self.schema, self.name], [data_type.name for data_type in self.data_types]


class StageFileIdent(SchemaObjectIdent):
    def __init__(self, env_prefix, database, schema, name, path):
        super().__init__(env_prefix, database, schema, name)

        self.path = path

    def parts_for_format(self):
        return [f"{self.env_prefix}{self.database}", self.schema, self.name], [self.path]


class TableConstraintIdent(SchemaObjectIdent):
    def __init__(self, env_prefix, database, schema, name, columns: List[Ident]):
        super().__init__(env_prefix, database, schema, name)

        self.columns = columns

    def parts_for_format(self):
        return [f"{self.env_prefix}{self.database}", self.schema, self.name], [str(c) for c in self.columns]
