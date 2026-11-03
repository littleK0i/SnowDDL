from typing import Optional, Union

SHOW_PAGE_SIZE = 10000


def iter_show_rows(engine, sql: str, params: Optional[dict] = None, page_size: int = SHOW_PAGE_SIZE):
    # SHOW commands are capped by ROWS_PER_RESULTSET, so results are retrieved in pages
    # using LIMIT ... FROM cursor supported by all SHOW commands returning "name" column
    from_name = None

    while True:
        page_sql = f"{sql} LIMIT {{__page_size:d}}"
        page_params = {**(params or {}), "__page_size": page_size}

        if from_name is not None:
            page_sql += " FROM {__from_name}"
            page_params["__from_name"] = from_name

        rows = list(engine.execute_meta(page_sql, page_params))

        yield from rows

        if len(rows) < page_size:
            return

        from_name = rows[-1]["name"]


def coalesce(val, default=None):
    return default if val is None else val


def compare_dynamic_param_value(bp_value: Union[bool, int, float, str], existing_value: str) -> bool:
    if isinstance(bp_value, bool):
        if bp_value is True and existing_value == "true":
            return True

        if bp_value is False and existing_value == "false":
            return True

    elif isinstance(bp_value, int):
        if bp_value == int(existing_value):
            return True

    elif isinstance(bp_value, float):
        if bp_value == float(existing_value):
            return True

    else:
        if str(bp_value) == existing_value:
            return True

    return False


def dtypes_from_arguments(arguments: str) -> str:
    all_dtypes = []

    start_dtypes_idx = arguments.index("(")
    finish_dtypes_idx = arguments.index(") RETURN ")

    for dtype_part in split_by_comma_outside_parentheses(arguments[start_dtypes_idx + 1 : finish_dtypes_idx]):
        # Remove optional DEFAULT prefix from the beginning
        dtype_part = dtype_part.removeprefix("DEFAULT ")

        # Remove optional data type size introduced in bundle 2025_03
        # https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_03/bcr-1944
        dtype_size_start_idx = dtype_part.find("(")

        if dtype_size_start_idx > -1:
            dtype_part = dtype_part[:dtype_size_start_idx]

        all_dtypes.append(dtype_part)

    return ",".join(all_dtypes)


def split_by_comma_outside_parentheses(s: str):
    parts = []
    current = []
    depth = 0

    for char in s:
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []

        else:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1

            current.append(char)

    if current:
        parts.append("".join(current).strip())

    return parts
