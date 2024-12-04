from abc import ABC, abstractmethod
from pathlib import Path
from string import ascii_letters, digits
from typing import List, Optional, Tuple

from .data_type import BaseDataType


class AbstractIdent(ABC):
    allowed_chars = set(ascii_letters + digits + "_$")

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

        return ".".join(core_parts)

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return f"<{self.__class__.__name__}={str(self)}>"

    def __eq__(self, other):
        if isinstance(other, AbstractIdent):
            return str(self) == str(other)

        if isinstance(other, str):
            return str(self) == other

        if other is None:
            return False

        raise NotImplementedError

    def _validate_part(self, val):
        val = str(val)

        if not val:
            raise ValueError("Identifier cannot be empty")

        for char in val:
            if char not in self.allowed_chars:
                raise ValueError(
                    f"Character [{char}] is not allowed in identifier [{val}], only ASCII letters, digits and single underscores are accepted"
                )

        return val.upper()


class AbstractIdentWithPrefix(AbstractIdent, ABC):
    def __init__(self, env_prefix):
        self.env_prefix = self._validate_env_prefix(env_prefix)

    def _validate_env_prefix(self, val):
        val = str(val)

        for char in val:
            if char not in self.allowed_chars:
                raise ValueError(
                    f"Character [{char}] is not allowed in env prefix [{val}], only ASCII letters, digits and single underscores are accepted"
                )

        if val and not val.endswith(("__", "_", "$")):
            raise ValueError(
                f"Env prefix [{val}] in identifier must end with valid separator like [__] double underscore, [_] single underscore or [$] dollar"
            )

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


class DatabaseRoleIdent(AbstractIdentWithPrefix):
    def __init__(self, env_prefix, database, name):
        super().__init__(env_prefix)

        self.database = self._validate_part(database)
        self.name = self._validate_part(name)

    def parts_for_format(self):
        return [f"{self.env_prefix}{self.database}", self.name], None

    @property
    def database_full_name(self):
        return DatabaseIdent(self.env_prefix, self.database)


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

    @property
    def schema_full_name(self):
        return SchemaIdent(self.env_prefix, self.database, self.schema)


class SchemaObjectIdentWithArgs(SchemaObjectIdent):
    def __init__(self, env_prefix, database, schema, name, data_types: List[BaseDataType]):
        super().__init__(env_prefix, database, schema, name)

        self.data_types = data_types

    def parts_for_format(self):
        return [f"{self.env_prefix}{self.database}", self.schema, self.name], [data_type.name for data_type in self.data_types]


class StageFileIdent(SchemaObjectIdent):
    def __init__(self, env_prefix, database, schema, name, path: Path):
        super().__init__(env_prefix, database, schema, name)

        self.path = path

    def parts_for_format(self):
        return [f"{self.env_prefix}{self.database}", self.schema, self.name], [self.path.as_posix()]

    @property
    def stage_full_name(self):
        return SchemaObjectIdent(self.env_prefix, self.database, self.schema, self.name)


class TableConstraintIdent(SchemaObjectIdent):
    def __init__(self, env_prefix, database, schema, name, columns: List[Ident]):
        super().__init__(env_prefix, database, schema, name)

        self.columns = columns

    def parts_for_format(self):
        return [f"{self.env_prefix}{self.database}", self.schema, self.name], [str(c) for c in self.columns]

    @property
    def table_full_name(self):
        return SchemaObjectIdent(self.env_prefix, self.database, self.schema, self.name)
