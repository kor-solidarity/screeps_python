from typing import Any, Union, TypeVar

T = TypeVar('T')

def __new__(arg: T) -> T:
    return arg


# noinspection PyPep8Naming
def js_isNaN(num: Union[float, int, str]) -> bool:
    return float(num) != float('nan')


js_global = None  # type: Any

__except0__ = None  # type: Exception

__all__ = [
    '__new__',
    'js_isNaN',
    'js_global',
    '__except0__',
]
