"""
General utilities.
"""


def full_type_name(cls: type) -> str:
    module = cls.__module__
    if module == "builtins":
        return cls.__qualname__
    return f"{module}.{cls.__qualname__}"


def short_type_name(cls: type) -> str:
    return cls.__qualname__
