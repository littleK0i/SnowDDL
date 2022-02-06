from hashlib import sha1
from typing import List, TYPE_CHECKING


if TYPE_CHECKING:
    from snowddl.engine import SnowDDLEngine


class SnowDDLQueryBuilder:
    def __init__(self, engine: "SnowDDLEngine"):
        self.engine = engine
        self.fragments: List[List[str]] = [[]]

    def append(self, sql, params=None):
        sql = self.engine.format(sql, params)
        self.fragments[-1].append(sql)

    def append_nl(self, sql, params=None):
        sql = self.engine.format(sql, params)
        self.fragments.append([sql])

    def fragment_count(self):
        return sum([len(f) for f in self.fragments])

    def short_hash(self):
        full_hash = sha1(str(self).encode('UTF-8')).hexdigest()
        short_hash = full_hash[:8]

        return f"#{short_hash}"

    def append_comment_short_hash(self, comment):
        if comment:
            return f"{comment} {self.short_hash()}"

        return self.short_hash()

    def compare_comment_short_hash(self, comment: str):
        if comment is None:
            return False

        return str(comment)[-9:] == self.short_hash()

    def __str__(self):
        return '\n'.join([' '.join(line) for line in self.fragments])
