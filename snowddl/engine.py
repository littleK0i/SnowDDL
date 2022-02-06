from logging import getLogger, NullHandler
from threading import get_ident

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from snowflake.connector import DictCursor, SnowflakeConnection, Error

from snowddl.config import SnowDDLConfig
from snowddl.settings import SnowDDLSettings
from snowddl.formatter import SnowDDLFormatter
from snowddl.query_builder import SnowDDLQueryBuilder
from snowddl.context import SnowDDLContext
from snowddl.error import SnowDDLExecuteError
from snowddl.schema_cache import SnowDDLSchemaCache


logger = getLogger(__name__)
logger.addHandler(NullHandler())


class SnowDDLEngine:
    def __init__(self, connection: SnowflakeConnection, config: SnowDDLConfig, settings: SnowDDLSettings):
        self.connection = connection
        self.config = config
        self.settings = settings

        self.formatter = SnowDDLFormatter()
        self.logger = logger

        self.executor = ThreadPoolExecutor(max_workers=self.settings.max_workers, thread_name_prefix=self.__class__.__name__)

        self.executed_ddl = []
        self.suggested_ddl = []

        self._executed_ddl_buffer = defaultdict(list)
        self._suggested_ddl_buffer = defaultdict(list)

        self.context = SnowDDLContext(self)
        self.schema_cache = SnowDDLSchemaCache(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown()

    def format(self, sql, params=None):
        sql = str(sql)

        if params:
            return self.formatter.format(sql, **params)

        return sql

    def query_builder(self):
        return SnowDDLQueryBuilder(self)

    def describe_meta(self, sql, params=None):
        return self._execute(sql, params, is_meta=True, is_describe=True)

    def execute_meta(self, sql, params=None):
        return self._execute(sql, params, is_meta=True)

    def execute_context_ddl(self, sql, params=None):
        return self._execute(sql, params)

    def execute_safe_ddl(self, sql, params=None, condition=True):
        if self.settings.execute_safe_ddl and condition:
            self._execute(sql, params)
        else:
            self._suggest(sql, params)

    def execute_unsafe_ddl(self, sql, params=None, condition=True):
        if self.settings.execute_unsafe_ddl and condition:
            self._execute(sql, params)
        else:
            self._suggest(sql, params)

    def flush_thread_buffers(self):
        for thread_sql in self._executed_ddl_buffer.values():
            for sql in thread_sql:
                self.executed_ddl.append(sql)

        for thread_sql in self._suggested_ddl_buffer.values():
            for sql in thread_sql:
                self.suggested_ddl.append(sql)

        self._executed_ddl_buffer = defaultdict(list)
        self._suggested_ddl_buffer = defaultdict(list)

    def _execute(self, sql, params, is_meta=False, is_describe=False):
        sql = self.format(sql, params)

        try:
            if is_describe:
                result = self.connection.cursor(DictCursor).describe(sql)
            else:
                result = self.connection.cursor(DictCursor).execute(sql)
        except Error as e:
            raise SnowDDLExecuteError(e, sql)

        if not is_meta:
            self._executed_ddl_buffer[get_ident()].append(sql)

        return result

    def _suggest(self, sql, params):
        sql = self.format(sql, params)
        self._suggested_ddl_buffer[get_ident()].append(sql)
