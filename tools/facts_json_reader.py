
from collections.abc import Callable
import json
from os import listdir, path
from typing import Iterator

from .get_names import domain_block_name, domain_entity_name, domain_item_name


"""LOOT TABLE
type
pools [
    rolls
    entries [
        type = item
        name
        functions? [
            function
            ...
|
type
pools [
    rolls
    entries [
        type = alternatives
        children [
            type = item
            name
            functions? [
                function
                ...    

"""


# =================================
ENTITY_LOOTTABLE_DIR = "minecraft/data/minecraft/loot_tables/entities"
BLOCK_LOOTTABLE_DIR = "minecraft/data/minecraft/loot_tables/blocks"

# =================================
def possible_drops(
        loot_table: dict,
        filter_func: Callable[[dict], bool] = lambda x: True
        ) -> Iterator[str]:
    def process(entry: dict):
        entry_type = entry.get("type")
        if entry_type == "minecraft:item":
            name = entry.get("name")
            if not filter_func(entry) or not name:
                return
            yield name
        elif entry_type == "minecraft:alternatives":
            for child in entry.get("children", []):
                yield from process(child)
    
    for pool in loot_table.get("pools", []):
        for entry in pool.get("entries", []):
            yield from process(entry)

def process_all_drops(
        loottable_dir: str,
        drops_func: Callable[[dict], Iterator[str]],
        naming_func: Callable[[str], str] 
        ) -> dict[str, list[str]]:
    """naming_func: generate name from bare identifier (filename without .json), e.g. b_stone from stone.json"""
    # TODO: support subdirs
    result = {}
    for filename in listdir(loottable_dir):
        full_path = path.join(loottable_dir, filename)
        if not path.isfile(full_path):
            continue
        with open(full_path, "r") as file:
            loot_table = json.load(file)
        name = naming_func(filename.removesuffix(".json"))
        drops = drops_func(loot_table)
        drops_names = set(domain_item_name(drop) for drop in drops)
        result[name] = sorted(drops_names)

    return result

# ----------------------
def possible_drops_mine(loot_table: dict) -> Iterator[str]:
    """Return all possible item IDs from a Minecraft loot table.\n
    For now, ignores all entries that require silk touch"""
    def filter_no_silk_touch(entry: dict) -> bool:
        if "conditions" not in entry:
            return True
        for condition in entry["conditions"]:
            if condition["condition"] != "minecraft:match_tool":
                return True
            if "predicate" not in condition:
                return True
            predicate = condition["predicate"]
            for enchantment in predicate.get("enchantments", []):
                if enchantment.get("type") == "minecraft:silk_touch":
                    return False
    return possible_drops(loot_table, filter_no_silk_touch)

def killed_becomes() -> dict[str, list[str]]:
    return process_all_drops(ENTITY_LOOTTABLE_DIR, possible_drops, domain_entity_name)
def mined_becomes() -> dict[str, list[str]]:
    return process_all_drops(BLOCK_LOOTTABLE_DIR, possible_drops_mine, domain_block_name)