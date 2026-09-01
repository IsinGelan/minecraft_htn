
import json
from typing import Iterator

from tools.helpers import as_list, remember

# ================================
TRANSLATION_FILEPATH = "minecraft/assets/minecraft/lang/en_us.json"

# ================================
def domain_item_name(mc_item_name: str) -> str:
    it = mc_item_name.removeprefix("minecraft:")
    return f"i_{it}"
def domain_block_name(mc_block_name: str) -> str:
    it = mc_block_name.removeprefix("minecraft:")
    return f"b_{it}"

# ================================
@remember
@as_list
def get_item_names() -> Iterator[str]:
    with open(TRANSLATION_FILEPATH, "r", encoding="utf-8") as f:
        data: dict[str, str] = json.load(f)
    for key, _ in data.items():
        if not key.startswith("item.minecraft."):
            continue
        it = key.removeprefix("item.minecraft.")
        if "." in it:
            # special item descriptions in language file
            continue
        yield domain_item_name(it)

@remember
@as_list
def get_block_names() -> Iterator[str]:
    with open(TRANSLATION_FILEPATH, "r", encoding="utf-8") as f:
        data: dict[str, str] = json.load(f)
    for key, _ in data.items():
        if not key.startswith("block.minecraft."):
            continue
        it = key.removeprefix("block.minecraft.")
        if "." in it:
            # special block descriptions in language file
            continue
        yield domain_block_name(it)

