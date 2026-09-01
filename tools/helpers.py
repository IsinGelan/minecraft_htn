
from typing import Callable, Iterator

def as_list[T](fun: Callable[..., Iterator[T]]) -> Callable[..., list[T]]:
    def wrapper(*args, **kwargs):
        res = fun(*args, **kwargs)
        if not isinstance(res, list):
            res = list(res)
        return res
    return wrapper

def remember[T](fun: Callable[[], T]) -> Callable[[], T]:
    """For remembering the value of a constant 0-adic function,
    so that it is only computed once."""
    res = ...
    def wrapper(*args, **kwargs):
        nonlocal res
        if res == ...:
            res = fun(*args, **kwargs)
        return res
    return wrapper