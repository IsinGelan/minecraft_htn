
import json
from typing import Iterator

from tools.helpers import as_list, remember

# ================================
TRANSLATION_FILEPATH = "minecraft/assets/minecraft/lang/en_us.json"

JAVA_ENTITY_TYPES_PATH = "minecraft_code/EntityType.java"

# ================================
def domain_item_name(mc_item_name: str) -> str:
    it = mc_item_name.removeprefix("minecraft:")
    return f"i_{it}"
def domain_block_name(mc_block_name: str) -> str:
    it = mc_block_name.removeprefix("minecraft:")
    return f"b_{it}"
def domain_entity_name(mc_entity_name: str) -> str:
    it = mc_entity_name.removeprefix("minecraft:")
    return f"e_{it}"
def domain_recipe_name(mc_recipe_name: str) -> str:
    it = mc_recipe_name.removeprefix("minecraft:")
    return f"r_{it}"
def block_to_item_name(block_name: str) -> str:
    """Get the corresponding item name for a block name"""
    assert block_name.startswith("b_")
    return "i_" + block_name.removeprefix("b_")

# ================================
@remember
@as_list
def get_item_item_names() -> Iterator[str]:
    """Get all item names that have a translation entry in the language file.\n
    This corresponds roughly to those items that do not have a block with the same name"""
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

@remember
def get_item_names() -> list[str]:
    """Get all existing item names, including
    items gotten from mining a block with the same name"""
    block_item_names = {block_to_item_name(block) for block in get_block_names()}
    as_set = set(get_item_item_names()) | block_item_names
    return list(as_set)

# ================================
REGISTRY_CALL = r'([A-Z_]+) = register\(\n?\s+("[^"]+")'

@remember
@as_list
def get_entity_names() -> Iterator[str]:
    """Get all entity names that are registered in EntityType.java"""
    with open(JAVA_ENTITY_TYPES_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    import re
    for match in re.finditer(REGISTRY_CALL, content):
        const_name, mc_entity_name = match.groups()
        mc_entity_name = mc_entity_name.strip('"')
        yield domain_entity_name(mc_entity_name)