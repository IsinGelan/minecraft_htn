
from shit_transpiler import transpile_domain, transpile_problem

from tools.generate_crafting import get_recipe_names
from tools.generate_prec_actions import domain_add_prec_action_calls, domain_add_prec_actions
from tools.get_names import get_block_names, get_entity_names, get_item_names
from tools.generate_facts import generate, get_structure_names
from tools.helpers import split_into_lines

MACRO_CONSTS_MARKER = "# MACRO CONSTS"
MACRO_FACTS_MARKER = "# MACRO FACTS"
BLOCK_TYPENAME = "Block"
ITEM_TYPENAME = "Item"
ENTITY_TYPENAME = "Entity"
RECIPE_TYPENAME = "Recipe"
STRUCTURE_TYPENAME = "Structure"

CONST_LINEWIDTH = 70

# ================================
def typed_declarations(typename: str, names: list[str]) -> str:
    """Generate a string of const declarations for the given names and typename"""
    names_string = " ".join(names)
    lines = [
        f"const {line} : {typename}\n"
        for line in split_into_lines(names_string, CONST_LINEWIDTH)]
    return "".join(lines)

def add_consts(code: str) -> str:
    blocks_decls = typed_declarations(BLOCK_TYPENAME, get_block_names())
    items_decls = typed_declarations(ITEM_TYPENAME, get_item_names())
    entity_decls = typed_declarations(ENTITY_TYPENAME, get_entity_names())
    recipe_decls = typed_declarations(RECIPE_TYPENAME, get_recipe_names())
    structure_decls = typed_declarations(STRUCTURE_TYPENAME, get_structure_names())

    const_decls = (
        blocks_decls
        + items_decls
        + entity_decls
        + recipe_decls
        + structure_decls
    )
    
    return code.replace(MACRO_CONSTS_MARKER, const_decls)

def add_domain_facts(code: str) -> str:
    facts_string = "\n".join(generate())
    return code.replace(MACRO_FACTS_MARKER, facts_string)


DOMAIN_MACRO_FUNS = [
    add_consts,
]
PROBLEM_MACRO_FUNS = [
    add_domain_facts,
]

# ================================
def main():
    domain = transpile_domain(
        "domain.shit",
        macro_funs=DOMAIN_MACRO_FUNS,
        show_macro_result=True)
    
    domain_add_prec_actions(domain)
    domain_add_prec_action_calls(domain)

    problem = transpile_problem(
        "idea_problem.shit",
        macro_funs=PROBLEM_MACRO_FUNS,
        show_macro_result=False)
    
    domain.write_to_file("domain.hddl")
    problem.write_to_file("problem.hddl")

if __name__ == "__main__":
    main()
