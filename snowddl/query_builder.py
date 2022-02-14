from base64 import urlsafe_b64encode
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

    def add_short_hash(self, comment):
        if comment:
            return f"{comment} {self._short_hash()}"

        return self._short_hash()

    def compare_short_hash(self, comment):
        if comment is None:
            return False

        return str(comment).endswith(self._short_hash())

    def _short_hash(self):
        sha1_digest = sha1(str(self).encode('UTF-8')).digest()
        return f"#{urlsafe_b64encode(sha1_digest[:12]).decode('ascii')}"

    def __str__(self):
        return '\n'.join([' '.join(line) for line in self.fragments])
