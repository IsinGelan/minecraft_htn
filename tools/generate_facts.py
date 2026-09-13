
from typing import Iterator

from .generate_crafting import recipe_result_items
from .facts_json_reader import mined_becomes, killed_becomes
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
STRUCTURE_DIMENSIONS = {
    "pillager_outpost": ["overworld"],
    "mineshaft": ["overworld"],
    # "mineshaft_mesa": ["overworld"],
    "mansion": ["overworld"],
    "jungle_pyramid": ["overworld"],
    "desert_pyramid": ["overworld"],
    "igloo": ["overworld"],
    "shipwreck": ["overworld"],
    # "shipwreck_beached": ["overworld"],
    "swamp_hut": ["overworld"],
    "stronghold": ["overworld"],
    "monument": ["overworld"],
    "ocean_ruin": ["overworld"], # not from the code; replacement for all variants
    # "ocean_ruin_cold": ["overworld"],
    # "ocean_ruin_warm": ["overworld"],
    "fortress": ["nether"],
    "nether_fossil": ["nether"],
    "end_city": ["end"],
    "buried_treasure": ["overworld"],
    "bastion_remnant": ["nether"],
    "village": ["overworld"], # not from the code; replacement for all variants
    # "village_plains": ["overworld"],
    # "village_desert": ["overworld"],
    # "village_savanna": ["overworld"],
    # "village_snowy": ["overworld"],
    # "village_taiga": ["overworld"],
    "ruined_portal": ["overworld", "nether"],
    # "ruined_portal_desert": ["overworld"],
    # "ruined_portal_jungle": ["overworld"],
    # "ruined_portal_swamp": ["overworld"],
    # "ruined_portal_mountain": ["overworld"],
    # "ruined_portal_ocean": ["overworld"],
    # "ruined_portal_nether": ["nether"],
}
# naturally spawned entities
ENTITY_DIMENSIONS = {
    "e_area_effect_cloud": [],
    "e_armor_stand": ["overworld"],
    "e_arrow": [],
    "e_bat": ["overworld"],
    "e_bee": ["overworld"],
    "e_blaze": ["nether"],
    "e_boat": [],
    "e_cat": ["overworld"],
    "e_cave_spider": ["overworld"],
    "e_chicken": ["overworld"],
    "e_cod": ["overworld"],
    "e_cow": ["overworld"],
    "e_creeper": ["overworld"],
    "e_dolphin": ["overworld"],
    "e_donkey": ["overworld"],
    "e_dragon_fireball": [],
    "e_drowned": ["overworld"],
    "e_elder_guardian": ["overworld"],
    "e_end_crystal": ["end"],
    "e_ender_dragon": ["end"],
    "e_enderman": ["overworld", "nether", "end"],
    "e_endermite": [],
    "e_evoker": [],
    "e_evoker_fangs": [],
    "e_experience_orb": [],
    "e_eye_of_ender": [],
    "e_falling_block": [],
    "e_firework_rocket": [],
    "e_fox": ["overworld"],
    "e_ghast": ["nether"],
    "e_giant": [],
    "e_guardian": ["overworld"],
    "e_hoglin": ["nether"],
    "e_horse": ["overworld"],
    "e_husk": ["overworld"],
    "e_illusioner": [],
    "e_iron_golem": ["overworld"],
    "e_item": ["overworld", "nether", "end"],
    "e_item_frame": [],
    "e_fireball": [],
    "e_leash_knot": [],
    "e_lightning_bolt": [],
    "e_llama": ["overworld"],
    "e_llama_spit": [],
    "e_magma_cube": ["nether"],
    "e_minecart": [],
    "e_chest_minecart": ["overworld"],
    "e_command_block_minecart": [],
    "e_furnace_minecart": [],
    "e_hopper_minecart": [],
    "e_spawner_minecart": [],
    "e_tnt_minecart": [],
    "e_mule": ["overworld"],
    "e_mooshroom": ["overworld"],
    "e_ocelot": ["overworld"],
    "e_painting": [],
    "e_panda": ["overworld"],
    "e_parrot": ["overworld"],
    "e_phantom": ["overworld"],
    "e_pig": ["overworld"],
    "e_piglin": ["nether"],
    "e_piglin_brute": ["nether"],
    "e_pillager": ["overworld"],
    "e_polar_bear": ["overworld"],
    "e_tnt": [],
    "e_pufferfish": ["overworld"],
    "e_rabbit": ["overworld"],
    "e_ravager": [],
    "e_salmon": ["overworld"],
    "e_sheep": ["overworld"],
    "e_shulker": ["end"],
    "e_shulker_bullet": [],
    "e_silverfish": ["overworld"],
    "e_skeleton": ["overworld", "nether"],
    "e_skeleton_horse": [],
    "e_slime": ["overworld"],
    "e_small_fireball": [],
    "e_snow_golem": [],
    "e_snowball": [],
    "e_spectral_arrow": [],
    "e_spider": ["overworld"],
    "e_squid": ["overworld"],
    "e_stray": ["overworld"],
    "e_strider": ["overworld"],
    "e_egg": [],
    "e_ender_pearl": [],
    "e_experience_bottle": [],
    "e_potion": [],
    "e_trident": [],
    "e_trader_llama": ["overworld"],
    "e_tropical_fish": ["overworld"],
    "e_turtle": ["overworld"],
    "e_vex": [],
    "e_villager": ["overworld"],
    "e_vindicator": ["overworld"],
    "e_wandering_trader": ["overworld"],
    "e_witch": ["overworld"],
    "e_wither": [],
    "e_wither_skeleton": ["nether"],
    "e_wither_skull": [],
    "e_wolf": ["overworld"],
    "e_zoglin": [],
    "e_zombie": ["overworld"],
    "e_zombie_horse": [],
    "e_zombie_villager": ["overworld"],
    "e_zombified_piglin": ["overworld"],
    "e_player": [],
    "e_fishing_bobber": [],
}
# ================================
# pred findable_block_in_dim(btype: Block, dim: Dim)
def generate_findable_block_in_dim() -> Iterator[str]:
    # TODO: where to find this?
    yield from []

# # pred can_reap_block(tool: Tool, btype: Block)
# def generate_can_reap_block() -> Iterator[str]:
#     # TODO: where to find this?
#     yield from []

# # pred reaped_block_becomes(btype: Block, item: Item)
# def generate_reaped_block_becomes() -> Iterator[str]:
#     # TODO: where to find this?
#     yield from []

# pred mined_becomes(btype: Block, item: Item)
def generate_mined_becomes() -> Iterator[str]:
    # TODO: where to find this?
    mined_becomes_dict = mined_becomes()
    for block, possible_drops in mined_becomes_dict.items():
        for drop in possible_drops:
            yield f"mined_becomes({block}, {drop})"

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
    for entity, dims in ENTITY_DIMENSIONS.items():
        for dim in dims:
            yield f"findable_entity_in_dim({entity}, {dim})"

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
    killed_becomes_dict = killed_becomes()
    for entity, possible_drops in killed_becomes_dict.items():
        for drop in possible_drops:
            yield f"killed_becomes({entity}, {drop})"

# pred findable_structure_in_dim(structure: Structure, dim: Dim)
def generate_findable_structure_in_dim() -> Iterator[str]:
    for structure, dims in STRUCTURE_DIMENSIONS.items():
        for dim in dims:
            yield f"findable_structure_in_dim({structure}, {dim})"

# pred leads_to(portal: Portal, dim: Dim)
def generate_leads_to() -> Iterator[str]:
    for portal, dim in PORTAL_LEADS_TO.items():
        yield f"leads_to({portal}, {dim})"

def generate_recipe_produces() -> Iterator[str]:
    for recipe, item in recipe_result_items().items():
        yield f"recipe_produces({recipe}, {item})"


# ================================
def generate() -> Iterator[str]:
    yield from generate_findable_block_in_dim()
    # yield from generate_can_reap_block()
    # yield from generate_reaped_block_becomes()
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
    yield from generate_recipe_produces()
    

def count_generated_facts() -> int:
    i = 0
    for _ in generate():
        i += 1
    return i

def domain_facts_to_file(path: str = "domain_facts.txt"):
    sorted_facts = sorted(generate())
    with open(path, "w", encoding="utf-8") as file:
        for fact in sorted_facts:
            file.write(f"{fact}\n")