
from typing import Iterator

from .get_names import block_to_item_name, get_block_names, get_item_names
from .code_extraction import BLOCK_REGISTRY

# ================================
MINING_TIER_3 = [
    "b_obsidian",
    "b_crying_obsidian",
    "b_netherite_block",
    "b_respawn_anchor",
    "b_ancient_debris"
]
MINING_TIER_2 = [
    "b_diamond_block",
    "b_diamond_ore",
    "b_emerald_block",
    "b_emerald_ore",
    "b_gold_block",
    "b_gold_ore",
    "b_redstone_ore"
]
MINING_TIER_1 = [
    "b_iron_block",
    "b_iron_ore",
    "b_lapis_block",
    "b_lapis_ore"
]
MINING_TIER_0 = {
    f"b_{name}"
    for (_, name, material) in BLOCK_REGISTRY.values()
    if material in ("STONE", "METAL", "HEAVY_METAL")
    or name == "nether_gold_ore"
}
PICKAXES = [
    "i_wooden_pickaxe",
    "i_stone_pickaxe",
    "i_iron_pickaxe",
    "i_diamond_pickaxe",
    "i_gold_pickaxe",
    "i_netherite_pickaxe"
]
MAX_TIER = {
    "i_wooden_pickaxe": 0,
    "i_stone_pickaxe": 1,
    "i_iron_pickaxe": 2,
    "i_diamond_pickaxe": 3,
    "i_gold_pickaxe": 0,
    "i_netherite_pickaxe": 3
}
BLOCK_MATERIALS = {
    f"b_{name}": material
    for (_, name, material) in BLOCK_REGISTRY.values()
}
PORTAL_LEADS_TO = {
    "nether_portal_nether": "overworld",
    "nether_portal_overworld": "nether",
    "lit_end_portal": "end",
    "lit_center_portal": "overworld"
}
# For most blocks, there is no corresponding item with a translation entry
PLACED_BECOMES = {
    block_to_item_name(block) : block
    for block in get_block_names()
}

# ================================
# pred findable_block_in_dim(btype: Block, dim: Dim)
def generate_findable_block_in_dim() -> Iterator[str]:
    # TODO: where to find this?
    yield from []

# pred can_reap_block(tool: Tool, btype: Block)
def generate_can_reap_block() -> Iterator[str]:
    # TODO: where to find this?
    yield from []

# pred reaped_block_becomes(btype: Block, item: Item)
def generate_reaped_block_becomes() -> Iterator[str]:
    # TODO: where to find this?
    yield from []

# pred mined_becomes(btype: Block, item: Item)
def generate_mined_becomes() -> Iterator[str]:
    # TODO: where to find this?
    yield from []

# pred mining_requires_tier(btype: Block, tier: ToolTier)
def generate_mining_requires_tier() -> Iterator[str]:
    """would be nicer to generate directly from the assets,
    but this info is only found in the source code"""
    # (!blockState.is(Blocks.IRON_BLOCK) && !blockState.is(Blocks.IRON_ORE) && !blockState.is(Blocks.LAPIS_BLOCK) && !blockState.is(Blocks.LAPIS_ORE)
    for block in MINING_TIER_3:
        # diamond
        yield f"mining_requires_tier({block}, tool_tier_3)"
    for block in MINING_TIER_2:
        # iron
        yield f"mining_requires_tier({block}, tool_tier_2)"
    for block in MINING_TIER_1:
        # stone
        yield f"mining_requires_tier({block}, tool_tier_1)"
    for block in MINING_TIER_0:
        yield f"mining_requires_tier({block}, tool_tier_0)"

# pred is_pickaxe(tool: Tool)
def generate_is_pickaxe() -> Iterator[str]:
    for pickaxe in PICKAXES:
        yield f"is_pickaxe({pickaxe})"

# pred can_mine_tier(tool: Tool, tier: ToolTier)
def generate_can_mine_tier() -> Iterator[str]:
    for tool, max_tier in MAX_TIER.items():
        for i in range(max_tier+1):
            yield f"can_mine_tier({tool}, tool_tier_{i})"

# pred placed_becomes(item: Item, btype: Block)
def generate_placed_becomes() -> Iterator[str]:
    # TODO: where to find this?
    for item, block in PLACED_BECOMES.items():
        yield f"placed_becomes({item}, {block})"

# pred findable_entity_in_dim(entity: Entity, dim: Dim)
def generate_findable_entity_in_dim() -> Iterator[str]:
    # TODO: where to find this?
    yield from []

# pred can_reap_entity(tool: Tool, etype: Entity)
def generate_can_reap_entity() -> Iterator[str]:
    # TODO: where to find this?
    yield from []

# pred reaped_entity_becomes(etype: Entity, item: Item)
def generate_reaped_entity_becomes() -> Iterator[str]:
    # TODO: where to find this?
    yield from []

# pred killed_becomes(entity: Entity, item: Item)
def generate_killed_becomes() -> Iterator[str]:
    # TODO: where to find this?
    yield from []

# pred findable_structure_in_dim(structure: Structure, dim: Dim)
def generate_findable_structure_in_dim() -> Iterator[str]:
    # TODO: where to find this?
    yield from []

# pred leads_to(portal: Portal, dim: Dim)
def generate_leads_to() -> Iterator[str]:
    for portal, dim in PORTAL_LEADS_TO.items():
        yield f"leads_to({portal}, {dim})"

# pred recipe_produces(recipe: Recipe, item: Item)


# ================================
def generate() -> Iterator[str]:
    yield from generate_findable_block_in_dim()
    yield from generate_can_reap_block()
    yield from generate_reaped_block_becomes()
    yield from generate_mined_becomes()
    yield from generate_mining_requires_tier()
    yield from generate_is_pickaxe()
    yield from generate_can_mine_tier()
    yield from generate_placed_becomes()
    yield from generate_findable_entity_in_dim()
    yield from generate_can_reap_entity()
    yield from generate_reaped_entity_becomes()
    yield from generate_killed_becomes()
    yield from generate_findable_structure_in_dim()
    yield from generate_leads_to()
    

def count_generated_facts() -> int:
    i = 0
    for _ in generate():
        i += 1
    return i