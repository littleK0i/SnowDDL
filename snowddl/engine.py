from logging import getLogger, NullHandler
from threading import get_ident as threading_get_ident

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from snowflake.connector import DictCursor, SnowflakeConnection, Error

from snowddl.cache import IntentionCache, SchemaCache
from snowddl.config import SnowDDLConfig
from snowddl.settings import SnowDDLSettings
from snowddl.formatter import SnowDDLFormatter
from snowddl.query_builder import SnowDDLQueryBuilder
from snowddl.context import SnowDDLContext
from snowddl.error import SnowDDLExecuteError


logger = getLogger(__name__)
logger.addHandler(NullHandler())


class SnowDDLEngine:
    def __init__(self, connection: SnowflakeConnection, config: SnowDDLConfig, settings: SnowDDLSettings):
        self.connection = connection
        self.config = config
        self.settings = settings
        self.logger = logger

        self.formatter = SnowDDLFormatter()
        self.format = self.formatter.format_sql

        self.executor = ThreadPoolExecutor(max_workers=self.settings.max_workers, thread_name_prefix=self.__class__.__name__)

        self.executed_ddl = []
        self.suggested_ddl = []

        self._executed_ddl_buffer = defaultdict(list)
        self._suggested_ddl_buffer = defaultdict(list)

        self.context = SnowDDLContext(self)
        self.context.activate_role_with_prefix()

        self.intention_cache = IntentionCache(self)
        self.schema_cache = SchemaCache(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown()

    def query_builder(self):
        return SnowDDLQueryBuilder(self.formatter)

    def describe_meta(self, sql, params=None):
        return self._describe(sql, params)

    def execute_meta(self, sql, params=None):
        return self._execute(sql, params, is_meta=True)

    def execute_clone(self, sql, params=None):
        return self._execute(sql, params)

    def execute_context_ddl(self, sql, params=None):
        return self._execute(sql, params)

    def execute_safe_ddl(self, sql, params=None, condition=True, file_stream=None):
        if self.settings.execute_safe_ddl and condition:
            self._execute(sql, params, False, file_stream)
        else:
            self._suggest(sql, params)

    def execute_unsafe_ddl(self, sql, params=None, condition=True, file_stream=None):
        if self.settings.execute_unsafe_ddl and condition:
            self._execute(sql, params, False, file_stream)
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

    def _execute(self, sql, params, is_meta=False, file_stream=None):
        sql = self.format(sql, params)

        try:
            result = self.connection.cursor(DictCursor).execute(sql, file_stream=file_stream)
        except Error as e:
            raise SnowDDLExecuteError(e, sql)

        if not is_meta:
            self._executed_ddl_buffer[threading_get_ident()].append(sql)

        return result

    def _describe(self, sql, params):
        sql = self.format(sql, params)

        try:
            result = self.connection.cursor(DictCursor).describe(sql)
        except Error as e:
            raise SnowDDLExecuteError(e, sql)

        return result

    def _suggest(self, sql, params):
        sql = self.format(sql, params)
        self._suggested_ddl_buffer[threading_get_ident()].append(sql)
