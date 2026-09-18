
# As data for block generation are manifold and hard to extract from the code, we will manually classify them

import json
from typing import Iterator
from os import path

from tools.get_names import get_block_names

from .helpers import as_dict

KEYS = "1234567890qwertyuiopasdfghjkl"

@as_dict
def classify[T](entries: list[T], options: list[str]) -> Iterator[tuple[T, list[str]]]:
    """Manually classify all entries"""
    assert len(options) <= len(KEYS), "Too many options for classification"

    print("Classify entries; Options (multiple allowed):")
    for i, option in enumerate(options, start=1):
        print(f"  {KEYS[i-1]}) {option}")
    print()

    for entry in entries:
        res = input(f"{entry}: ")
        selected = [options[KEYS.index(c)] for c in res if c in KEYS]
        yield entry, selected

# ================================
BLOCKS_CLASSIFICATION_PATH = "data/block_dimensions.json"

def classify_blocks() -> dict[str, list[str]]:
    blocks = get_block_names()
    options = ["overworld", "nether", "end"]
    res = classify(blocks, options)
    with open(BLOCKS_CLASSIFICATION_PATH, "w") as file:
        json.dump(res, file, indent=4)
    return res

def block_dimensions() -> dict[str, list[str]]:
    if not path.exists(BLOCKS_CLASSIFICATION_PATH):
        return classify_blocks()
    with open(BLOCKS_CLASSIFICATION_PATH, "r") as file:
        res = json.load(file)
    return res