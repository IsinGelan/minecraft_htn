from typing import Iterator

from shit_transpiler import transpile_file_to_file
from tools.get_names import get_block_names, get_item_names
# import shit_transpiler

MACRO_CONSTS_MARKER = "# MACRO CONSTS"
BLOCK_TYPENAME = "Block"
ITEM_TYPENAME = "Item"
CONST_LINEWIDTH = 70

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
    yield text[line_start_index:next_space_index]

def add_consts(code: str) -> str:
    blocks_string = " ".join(get_block_names())
    blocks_lines = [
        f"const {line} : {BLOCK_TYPENAME}\n"
        for line in split_into_lines(blocks_string, CONST_LINEWIDTH)]
    items_string = " ".join(get_item_names())
    items_lines = [
        f"const {line} : {ITEM_TYPENAME}\n"
        for line in split_into_lines(items_string, CONST_LINEWIDTH)]

    const_string = "".join(blocks_lines) + "".join(items_lines)
    return code.replace(MACRO_CONSTS_MARKER, const_string)

MACRO_FUNS = [
    add_consts,
]

# ================================
def main():
    transpile_file_to_file(
        "domain.shit",
        "domain.hddl",
        macro_funs=MACRO_FUNS,
        show_macro_result=True)

if __name__ == "__main__":
    main()
