
from typing import Callable, Iterable, Iterator, Optional

# ================================
def find[T](iter: Iterable[T], pred: Callable[[T], bool]) -> Optional[T]:
    for item in iter:
        if pred(item):
            return item
    return None

def into_bins[T, Hashable](iter: Iterable[T], bin_key: Callable[[T], Hashable]) -> dict[Hashable, list[T]]:
    bins: dict[Hashable, list[T]] = {}
    for item in iter:
        key = bin_key(item)
        if key not in bins:
            bins[key] = []
        bins[key].append(item)
    return bins


# ================================
# Decorators
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