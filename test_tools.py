
from tools.get_names import get_block_names, get_item_names


items = get_item_names()
blocks = get_block_names()

# print(*items, sep="\n")
# print(len(items))
print(*blocks, sep="\n")
print(len(blocks))