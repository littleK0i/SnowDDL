from fnmatch import translate
from re import compile
from string import ascii_letters, digits
from typing import List, Pattern

from snowddl.blueprint.ident import AbstractIdentWithPrefix


class IdentPattern:
    allowed_chars_pattern = set(ascii_letters + digits + "_$()." + "|!*?[]")
    special_chars_complex_pattern = set("|!*?[]")

    def __init__(self, pattern):
        self.pattern = self._validate_pattern(pattern)
        self.is_complex_pattern = self._is_complex_pattern(pattern)

        self.include_regexp: List[Pattern] = []
        self.exclude_regexp: List[Pattern] = []

        if self.is_complex_pattern:
            for sub_pattern in self.pattern.split("|"):
                is_exclude = False

                if sub_pattern.startswith("!"):
                    is_exclude = True
                    sub_pattern = sub_pattern[1:]

                if not sub_pattern:
                    continue

                compiled_regexp = compile(translate(sub_pattern))

                if is_exclude:
                    self.exclude_regexp.append(compiled_regexp)
                else:
                    self.include_regexp.append(compiled_regexp)

            if not self.include_regexp:
                raise ValueError(f"Identifier pattern [{self.pattern}] does not contain any positive sub-patterns")

    @classmethod
    def build_from_ident(cls, ident: AbstractIdentWithPrefix):
        return cls(cls._get_str_ident_without_prefix(ident))

    def is_match_ident(self, ident: AbstractIdentWithPrefix) -> bool:
        str_ident_without_prefix = self._get_str_ident_without_prefix(ident)

        if self.is_complex_pattern:
            is_match_include = any(regexp.match(str_ident_without_prefix) for regexp in self.include_regexp)
            is_match_exclude = any(regexp.match(str_ident_without_prefix) for regexp in self.exclude_regexp)

            return is_match_include and not is_match_exclude

        return str_ident_without_prefix == self.pattern

    def __str__(self):
        return self.pattern

    def __repr__(self):
        return f"<{self.__class__.__name__}={str(self)}>"

    def _is_complex_pattern(self, val):
        return any(char in self.special_chars_complex_pattern for char in val)

    @classmethod
    def _get_str_ident_without_prefix(cls, ident: AbstractIdentWithPrefix):
        return str(ident).removeprefix(ident.env_prefix)

    def _validate_pattern(self, val):
        val = str(val)

        if not val:
            raise ValueError("Pattern cannot be empty")

        for char in val:
            if char not in self.allowed_chars_pattern:
                raise ValueError(
                    f"Character [{char}] is not allowed in identifier pattern [{val}], "
                    f"only ASCII letters, digits, single underscores and Unix-style pattern characters are accepted"
                )

        return val.upper()
