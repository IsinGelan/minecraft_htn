
from os import path
from typing import Callable, Iterable, Iterator, Optional

from pydantic import BaseModel

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
def split_into_lines(text: str, line_length: int) -> Iterator[str]:
    """yields line and starts new one as soon as the line length is exceeded.
    Splits on spaces"""
    text_len = len(text)

    line_start_index = 0
    line_end_index = 0
    text_index = 0
    while text_index < text_len - 1:
        next_space_index = text.find(" ", line_end_index)
        if next_space_index == -1:
            next_space_index = text_len
        text_index = line_end_index = next_space_index + 1
        if line_end_index - line_start_index > line_length:
            yield text[line_start_index:line_end_index-1]
            line_start_index = line_end_index
    if line_start_index >= text_len:
        return
    yield text[line_start_index:next_space_index]

# ================================
# Decorators
def as_list[T](fun: Callable[..., Iterable[T]]) -> Callable[..., list[T]]:
    def wrapper(*args, **kwargs):
        res = fun(*args, **kwargs)
        if not isinstance(res, list):
            res = list(res)
        return res
    return wrapper

def as_dict[T1, T2](fun: Callable[..., Iterable[tuple[T1, T2]]]) -> Callable[..., dict[T1, T2]]:
    def wrapper(*args, **kwargs):
        res = fun(*args, **kwargs)
        if not isinstance(res, dict):
            res = dict(res)
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

# ================================
class Registry[T](BaseModel):
    """A dictionary of values that are interdependent, i.e. the computation of
    one value may require the prior computation of another value.\n
    The Registry takes care of this and computes values when needed.\n
    To use the Registry, subclass it and implement the compute method"""
    _items: dict[str, T] = {}

    def compute(self, name: str) -> T:
        ...

    def get(self, name: str) -> T:
        if name not in self._items:
            self._items[name] = self.compute(name)
        return self._items.get(name)

    def get_for_all(self, names: list[str]) -> list[T]:
        return [self._items[name] for name in names]

    def entries(self) -> list[T]:
        return list(self._items.values())

# ================================
def read_or_compute[T](
        file_path: str, *,
        read_fun: Callable[[str], T],
        compute_fun: Callable[[], T],
        write_fun: Callable[[T], str]
    ):
    if not path.exists(file_path):
        res = compute_fun()
        with open(file_path, "w") as f:
            f.write(write_fun(res))
    else:
        with open(file_path, "r") as f:
            res = read_fun(f.read())
    return res