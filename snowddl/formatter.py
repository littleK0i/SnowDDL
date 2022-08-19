import re
import string

from snowddl.blueprint import AbstractIdent


class SnowDDLFormatter(string.Formatter):
    safe_ident_regexp = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
    safe_decimal_regexp = re.compile(r'^[+-]?[0-9]+(\.[0-9]+)?$')
    safe_float_regexp = re.compile(r'^[+-]?[0-9]+(\.[0-9]+([e|E][+-][0-9]+)?)?$')

    def __init__(self):
        self.smart_transformations = {
            's': self.quote,
            'd': self.safe_decimal,
            'f': self.safe_float,
            'b': self.safe_bool,
            'i': self.quote_ident,
            'in': self.quote_ident_no_argument,
            'r': str,
            'lf': self.quote_like_full_match,
            'ls': self.quote_like_starts_with,
            'le': self.quote_like_ends_with,
            'lse': self.quote_like_starts_ends_with,
        }

        self.raw_transformations = {
            'dp': self.dynamic_param,
        }

        self.default_transformation = 's'

    def format_sql(self, sql, params=None):
        sql = str(sql)

        if params:
            return self.vformat(sql, [], params)

        return sql

    def convert_field(self, value, conversion):
        if conversion is not None:
            raise ValueError("Conversions are disabled for SnowDDLFormatter")

        return value

    def format_field(self, value, format_spec):
        if not format_spec:
            format_spec = self.default_transformation

        if format_spec in self.raw_transformations:
            return self.raw_transformations[format_spec](value)

        if format_spec not in self.smart_transformations:
            raise ValueError(f"Unknown format transformation [{format_spec}]")

        if isinstance(value, list) and format_spec != 'dp':
            if not value:
                raise ValueError("Attempt to format an empty list")
            return ', '.join([self.smart_transformations[format_spec](v) for v in value])
        else:
            return self.smart_transformations[format_spec](value)

    @classmethod
    def escape(cls, val):
        return str(val).replace("'", "''").replace("\\", "\\\\")

    @classmethod
    def escape_ident(cls, val):
        val = str(val)

        if not val:
            raise ValueError("Identifier cannot be empty")

        return val.replace('"', '""')

    @classmethod
    def escape_like(cls, val):
        return str(val).replace("_", "\\_").replace("%", "\\%")

    @classmethod
    def quote(cls, val):
        if val is None:
            return 'NULL'

        return f"'{cls.escape(val)}'"

    @classmethod
    def quote_ident(cls, val):
        if not isinstance(val, AbstractIdent):
            return f'"{cls.escape_ident(val)}"'

        core_parts, argument_parts = val.parts_for_format()

        if argument_parts is not None:
            return '.'.join(f'"{cls.escape_ident(p)}"' for p in core_parts) + \
                   '(' + ','.join(cls.safe_ident(p) for p in argument_parts) + ')'

        return '.'.join(f'"{cls.escape_ident(p)}"' for p in core_parts)

    @classmethod
    def quote_ident_no_argument(cls, val):
        if not isinstance(val, AbstractIdent):
            return f'"{cls.escape_ident(val)}"'

        core_parts, _ = val.parts_for_format()

        return '.'.join(f'"{cls.escape_ident(p)}"' for p in core_parts)

    @classmethod
    def quote_like_full_match(cls, val):
        return cls.quote(f"{cls.escape_like(val)}")

    @classmethod
    def quote_like_starts_with(cls, val):
        return cls.quote(f"{cls.escape_like(val)}%")

    @classmethod
    def quote_like_ends_with(cls, val):
        return cls.quote(f"%{cls.escape_like(val)}")

    @classmethod
    def quote_like_starts_ends_with(cls, val):
        return cls.quote(f"{cls.escape_like(val[0])}%{cls.escape_like(val[1])}")

    @classmethod
    def safe_ident(cls, val):
        val = str(val)

        if not cls.safe_ident_regexp.match(val):
            raise ValueError(f"Value [{val}] is not a safe identifier")

        return val.upper()

    @classmethod
    def safe_float(cls, val):
        if val is None:
            return 'NULL'

        val = str(val)

        if not cls.safe_float_regexp.match(val):
            raise ValueError(f'Value [{val}] is not a safe float')

        return val

    @classmethod
    def safe_decimal(cls, val):
        if val is None:
            return 'NULL'

        val = str(val)

        if not cls.safe_decimal_regexp.match(val):
            raise ValueError(f'Value [{val}] is not a safe integer')

        return val

    @classmethod
    def safe_bool(cls, val):
        if not isinstance(val, bool):
            raise ValueError(f'Value [{val}] is not a safe boolean')

        return 'TRUE' if val else 'FALSE'

    @classmethod
    def dynamic_param(cls, val):
        if isinstance(val, list):
            return f"({', '.join([cls.dynamic_param(v) for v in val])})"
        elif isinstance(val, bool):
            return cls.safe_bool(val)
        elif isinstance(val, int):
            return cls.safe_decimal(val)
        elif isinstance(val, float):
            return cls.safe_float(val)
        else:
            return cls.quote(val)
