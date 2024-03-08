from typing import Union


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
    arguments = arguments.replace("DEFAULT ", "")
    arguments = arguments.translate(str.maketrans("", "", "[] "))

    start_dtypes_idx = arguments.index("(")
    finish_dtypes_idx = arguments.index(")")

    return ",".join(a for a in arguments[start_dtypes_idx + 1 : finish_dtypes_idx].split(","))
