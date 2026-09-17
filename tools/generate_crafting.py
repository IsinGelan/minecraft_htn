
import json
from os import listdir, path
from typing import Iterator, Literal, Self

from pydantic import BaseModel

from .helpers import as_dict, as_list, remember
from .get_names import domain_item_name, domain_recipe_name

# RECIPE_DIR = path.join(path.dirname(__file__), "..", "minecraft", "data", "minecraft", "recipes")
RECIPE_DIR = "minecraft/data/minecraft/recipes/"

FurnaceType = Literal["smelting", "smoking", "blasting"]

CRAFTING_PATTERN_NEXTLINE = "\n"
AIR_ITEM = "minecraft:air"

# ================================
class Recipe(BaseModel):
    recipe_name: str
    result_item: str
    result_count: int

    @classmethod
    def from_dict(cls, dic: dict, name: str) -> Self:
        ...
    def generate_action_numbered(self):
        ...
    def generate_action_unnumbered(self):
        print(f"Fallback for {self.recipe_name}")
        ...


class StonecuttingRecipe(Recipe):
    ingredient: str

    @classmethod
    def from_dict(cls, dic: dict, name: str) -> Self:
        return cls(
            recipe_name=name,
            result_item=dic["result"],
            result_count=dic.get("count", 1),
            ingredient=dic["ingredient"]["item"]
        )
    def generate_action_numbered(self):
        return f"action recipe_{self.recipe_name}\n" \
                "    < near_block(b_stonecutter)\n" \
               f"    < item_nr({domain_item_name(self.ingredient)}) >= 1\n" \
               f"    => item_nr({domain_item_name(self.ingredient)}) -= 1\n" \
               f"    => item_nr({domain_item_name(self.result_item)}) += {self.result_count}\n"
    def generate_action_unnumbered(self):
        return f"action recipe_{self.recipe_name}\n" \
                "    < near_block(b_stonecutter)\n" \
               f"    < has_item({domain_item_name(self.ingredient)})\n" \
               f"    => has_item({domain_item_name(self.result_item)})\n"
                

def item_tag_desc(item: dict | list) -> str:
    if isinstance(item, list):
        # For cases like soul_torch (option in key)
        # or fire_charge            (option in ingredients)
        item = item[0]
    if "tag" in item:
        return f"#{item['tag']}"
    else:
        return item['item']

def large_pattern(dic: dict) -> bool:
    if "ingredients" in dic:
        return len(dic["ingredients"]) > 4
    if len(dic["pattern"]) == 3:
        return True
    if any(len(row) == 3 for row in dic["pattern"]):
        return True
    return False

def pattern(dic: dict) -> tuple[str, ...]:
    if "ingredients" in dic:
        ingredients = dic["ingredients"]
        return tuple(item_tag_desc(ing) for ing in ingredients)

    key = {k: item_tag_desc(v) for k, v in dic["key"].items()} | {" ": AIR_ITEM}
    pattern = []
    for line in dic["pattern"]:
        for char in line:
            pattern.append(key[char])
        pattern.append(CRAFTING_PATTERN_NEXTLINE)
    return tuple(pattern[:-1])  # Remove last newline

def ingredients_from_pattern(pattern: tuple[str, ...]) -> list[tuple[str, int]]:
        counts: dict[str, int] = {}
        for item in pattern:
            if item == CRAFTING_PATTERN_NEXTLINE:
                continue
            if item == AIR_ITEM:
                continue
            counts[item] = counts.get(item, 0) + 1
        return [(item, count) for item, count in counts.items()]
            
class CraftingRecipe(Recipe):
    large_interface: bool
    ingredients: list[tuple[str, int]]
    pattern: tuple[str, ...]
    
    @classmethod
    def from_dict(cls, dic: dict, name: str) -> Self:
        pat = pattern(dic)
        ingredients = ingredients_from_pattern(pat)

        return cls(
            recipe_name=name,
            result_item=dic["result"]["item"],
            result_count=dic["result"].get("count", 1),
            large_interface=large_pattern(dic),
            ingredients=ingredients,
            pattern=pat
        )
    def generate_action_numbered(self):
        block_prec = "    < near_block(b_crafting_table)\n" if self.large_interface else ""
        item_prec = "".join(
            f"    < item_nr({domain_item_name(ing)}) >= {count}\n"
            for ing, count in self.ingredients
            )
        item_post = "".join(
            f"    => item_nr({domain_item_name(ing)}) -= {count}\n"
            for ing, count in self.ingredients
            )
        return f"action recipe_{self.recipe_name}\n" \
               f"{block_prec}" \
               f"{item_prec}" \
               f"{item_post}" \
               f"    => item_nr({domain_item_name(self.result_item)}) += {self.result_count}\n"
    def generate_action_unnumbered(self):
        block_prec = "    < near_block(b_crafting_table)\n" if self.large_interface else ""
        item_prec = "".join(
            f"    < has_item({domain_item_name(ing)})\n"
            for ing, count in self.ingredients
            )
        return f"action recipe_{self.recipe_name}\n" \
               f"{block_prec}" \
               f"{item_prec}" \
               f"    => has_item({domain_item_name(self.result_item)})\n"

class CampfireRecipe(Recipe):
    ingredient: str
    
    @classmethod
    def from_dict(cls, dic: dict, name: str) -> Self:
        return cls(
            recipe_name=name,
            result_item=dic["result"],
            result_count=dic.get("count", 1),
            ingredient=dic["ingredient"]["item"]
        )
    def generate_action_numbered(self):
        return f"action recipe_{self.recipe_name}\n" \
                "    < near_block(b_campfire)\n" \
               f"    < item_nr({domain_item_name(self.ingredient)}) >= 1\n" \
               f"    => item_nr({domain_item_name(self.ingredient)}) -= 1\n" \
               f"    => item_nr({domain_item_name(self.result_item)}) += {self.result_count}\n"
    def generate_action_unnumbered(self):
        return f"action recipe_{self.recipe_name}\n" \
                "    < near_block(b_campfire)\n" \
               f"    < has_item({domain_item_name(self.ingredient)})\n" \
               f"    => has_item({domain_item_name(self.result_item)})\n"

class FurnaceRecipe(Recipe):
    furnace_type: FurnaceType
    ingredient: str

    @classmethod
    def from_dict(cls, dic: dict, name: str) -> Self:
        if isinstance(dic["ingredient"], list):
            # Fix for for example minecraft/data/minecraft/recipes/gold_ingot
            dic["ingredient"] = dic["ingredient"][0]
        
        return cls(
            recipe_name=name,
            result_item=dic["result"],
            result_count=1,
            furnace_type=dic["type"].removeprefix("minecraft:"),
            ingredient=item_tag_desc(dic["ingredient"])
        )
    def generate_action_numbered(self):
        block_name = {
            "smelting": "b_furnace",
            "smoking": "b_smoker",
            "blasting": "b_blast_furnace"}
        return f"action recipe_{self.recipe_name}\n" \
               f"    < near_block({block_name[self.furnace_type]})\n" \
               f"    < item_nr({domain_item_name(self.ingredient)}) >= 1\n" \
               f"    => item_nr({domain_item_name(self.ingredient)}) -= 1\n" \
               f"    => item_nr({domain_item_name(self.result_item)}) += {self.result_count}\n"
    def generate_action_unnumbered(self):
        block_name = {
            "smelting": "b_furnace",
            "smoking": "b_smoker",
            "blasting": "b_blast_furnace"}
        return f"action recipe_{self.recipe_name}\n" \
               f"    < near_block({block_name[self.furnace_type]})\n" \
               f"    < has_item({domain_item_name(self.ingredient)})\n" \
               f"    => has_item({domain_item_name(self.result_item)})\n"

class SmithingRecipe(Recipe):
    base: str
    addition: str

    @classmethod
    def from_dict(cls, dic: dict, name: str) -> Self:
        return cls(
            recipe_name=name,
            result_item=dic["result"]["item"],
            result_count=dic["result"].get("count", 1),
            base=item_tag_desc(dic["base"]),
            addition=item_tag_desc(dic["addition"])
        )
    def generate_action_numbered(self):
        return f"action recipe_{self.recipe_name}\n" \
               f"    < near_block(b_smithing_table)\n" \
               f"    < item_nr({domain_item_name(self.base)}) >= 1\n" \
               f"    < item_nr({domain_item_name(self.addition)}) >= 1\n" \
               f"    => item_nr({domain_item_name(self.base)}) -= 1\n" \
               f"    => item_nr({domain_item_name(self.addition)}) -= 1\n" \
               f"    => item_nr({domain_item_name(self.result_item)}) += {self.result_count}\n"
    def generate_action_unnumbered(self):
        return f"action recipe_{self.recipe_name}\n" \
               f"    < near_block(b_smithing_table)\n" \
               f"    < has_item({domain_item_name(self.base)})\n" \
               f"    < has_item({domain_item_name(self.addition)})\n" \
               f"    => has_item({domain_item_name(self.result_item)})\n"


# ================================
def read_recipe_file(filename: str) -> Recipe:
    with open(filename, "r") as file:
        dic = json.load(file)
    typ = dic["type"]
    recipe_name = filename.removesuffix(".json").removeprefix(RECIPE_DIR)
    match typ:
        case "minecraft:stonecutting":
            return StonecuttingRecipe.from_dict(dic, recipe_name)
        case "minecraft:crafting_shaped":
            return CraftingRecipe.from_dict(dic, recipe_name)
        case "minecraft:crafting_shapeless":
            return CraftingRecipe.from_dict(dic, recipe_name)
        case "minecraft:campfire_cooking":
            return CampfireRecipe.from_dict(dic, recipe_name)
        case "minecraft:smelting":
            return FurnaceRecipe.from_dict(dic, recipe_name)
        case "minecraft:smoking":
            return FurnaceRecipe.from_dict(dic, recipe_name)
        case "minecraft:blasting":
            return FurnaceRecipe.from_dict(dic, recipe_name)
        case "minecraft:smithing":
            return SmithingRecipe.from_dict(dic, recipe_name)
        case _:
            print("Unhandled recipe type:", typ, "for recipe", recipe_name)
            return None

@remember
@as_list
def all_recipes() -> Iterator[Recipe]:
    for filename in listdir(RECIPE_DIR):
        filepath = path.join(RECIPE_DIR, filename)
        rec = read_recipe_file(filepath)
        if rec is not None:
            yield rec

def get_recipe_names() -> list[str]:
    return [domain_recipe_name(rec.recipe_name) for rec in all_recipes()]

@remember
@as_dict
def recipe_result_items() -> Iterator[tuple[str, str]]:
    for rec in all_recipes():
        yield domain_recipe_name(rec.recipe_name), domain_item_name(rec.result_item)


# ================================
RECIPE_CRAFTING_TASK_NAME = "craft-recipe"
ITEM_CRAFTING_TASK_NAME = "craft-item"

def generate_recipe_crafting_task(recipe_names: list[str]) -> str:
    task_str = f"task {RECIPE_CRAFTING_TASK_NAME}(recipe: Recipe)\n"
    method_strs = [
        f"{RECIPE_CRAFTING_TASK_NAME} : {recipe_name}(recipe: Recipe)\n" \
        f"    < recipe = {domain_recipe_name(recipe_name)}\n" \
        f"    - recipe_{recipe_name}\n"
        for recipe_name in recipe_names
    ]

    return task_str + "".join(method_strs)

def generate_item_crafting_task() -> str:
    task_str = f"task {ITEM_CRAFTING_TASK_NAME}(item: Item)\n"
    method_str = f"{ITEM_CRAFTING_TASK_NAME} : craft(recipe: Recipe, item: Item)\n" \
                 f"    < recipe_produces(recipe, item)\n" \
                 f"    - {RECIPE_CRAFTING_TASK_NAME}(recipe)\n"

    return task_str + method_str


# ================================
def recipes_string(*, numbered: bool) -> str:
    recipe_fun = lambda rec: rec.generate_action_numbered() if numbered else rec.generate_action_unnumbered()
    recipes = list(all_recipes())
    # TODO: Deal with item tags
    tagless_recipes = [rec for rec in recipes
                       if "#" not in rec.generate_action_unnumbered()]

    recipe_names = [rec.recipe_name for rec in tagless_recipes]
    recipe_task_str = generate_recipe_crafting_task(recipe_names)
    item_task_str   = generate_item_crafting_task()
    actions_str = "\n".join(
        recipe_fun(rec) for rec in tagless_recipes
    )
    return item_task_str + "\n\n" + recipe_task_str + "\n\n" + actions_str + "\n"

def recipes_to_file(filename: str, *, numbered: bool):
    with open(filename, "w") as file:
        file.write(recipes_string(numbered=numbered))

def main():
    recipes_to_file("recipes.shit", numbered=False)

if __name__ == "__main__":
    main()