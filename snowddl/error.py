from snowflake.connector.errors import Error


class SnowDDLExecuteError(Exception):
    def __init__(self, snow_exc: Error, sql: str):
        self.snow_exc = snow_exc
        self.sql = sql

    def verbose_message(self):
        params = {
            'message': self.snow_exc.raw_msg,
            'errno': self.snow_exc.errno,
            'sqlstate': self.snow_exc.sqlstate,
            'sfqid': self.snow_exc.sfqid,
            'sql': self.sql,
        }

        pad_length = max(len(x) for x in params)
        res = ''

        for k in params:
            res += f"    {k.ljust(pad_length)}  =>  {params[k]}\n"

        return '(\n' + res + ')'



class SnowDDLUnsupportedError(Exception):
    pass
