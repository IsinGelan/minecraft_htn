
from tools.get_names import get_block_names, get_item_names, get_entity_names
from tools.generate_crafting import recipes_to_file
from tools.generate_facts import domain_facts_to_file

items = get_item_names()
blocks = get_block_names()

# print(*items, sep="\n")
# print(len(items))
# print(*blocks, sep="\n")
# print(len(blocks))
# print(*generate(), sep="\n")
# print(count_generated_facts())

# print(*BLOCK_MATERIALS.items(), sep="\n")
# print(*generate_mining_requires_tier(), sep="\n")
print(*get_entity_names(), sep="\n")
print(len(get_entity_names()))

# print(*PLACED_BECOMES.items(), sep="\n")
recipes_to_file("recipes.shit")
domain_facts_to_file("domain_facts.txt")
