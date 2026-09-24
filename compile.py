
import argparse

from shitlang import transpile_domain, transpile_problem

from shitlang.shit_objs import DomainFile, ProblemFile
from tools.generate_crafting import get_recipe_names, recipes_string
from tools.generate_prec_actions import domain_do_precondition_replacement
from tools.get_names import get_block_names, get_entity_names, get_item_names
from tools.generate_facts import PICKAXES, generate, get_block_tag_names, get_item_tag_names, get_structure_names
from tools.helpers import split_into_lines

MACRO_CONSTS_MARKER = "# MACRO CONSTS"
MACRO_FACTS_MARKER = "# MACRO FACTS"
MACRO_CRAFTING_MARKER = "# MACRO CRAFTING"
BLOCK_TYPENAME = "Block"
ITEM_TYPENAME = "Item"
ENTITY_TYPENAME = "Entity"
RECIPE_TYPENAME = "Recipe"
STRUCTURE_TYPENAME = "Structure"
ITEM_TAG_TYPENAME = "ItemTag"
BLOCK_TAG_TYPENAME = "BlockTag"
ENTITY_TAG_TYPENAME = "EntityTag"

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
    items_decls = typed_declarations(ITEM_TYPENAME, set(get_item_names()) - set(PICKAXES))
    entity_decls = typed_declarations(ENTITY_TYPENAME, get_entity_names())
    recipe_decls = typed_declarations(RECIPE_TYPENAME, get_recipe_names())
    item_tag_decls = typed_declarations(ITEM_TAG_TYPENAME, get_item_tag_names())
    # block_tag_decls = typed_declarations(BLOCK_TAG_TYPENAME, get_block_tag_names())
    structure_decls = typed_declarations(STRUCTURE_TYPENAME, get_structure_names())
    # entity_tag_decls = typed_declarations(ENTITY_TAG_TYPENAME, get_entity_tag_names())

    const_decls = (
        blocks_decls
        + items_decls
        + entity_decls
        + recipe_decls
        + structure_decls
        + item_tag_decls
        # + block_tag_decls
    )
    
    return code.replace(MACRO_CONSTS_MARKER, const_decls)

def add_crafting_recipes(code: str) -> str:
    recipes_str = recipes_string(numbered=False)
    return code.replace(MACRO_CRAFTING_MARKER, recipes_str)

def add_domain_facts(code: str) -> str:
    facts_string = "\n".join(generate())
    return code.replace(MACRO_FACTS_MARKER, facts_string)


DOMAIN_MACRO_FUNS = [
    add_consts,
    add_crafting_recipes,
]
PROBLEM_MACRO_FUNS = [
    add_domain_facts,
]

# ================================
ARGPARSER = argparse.ArgumentParser(prog="Minecraft SHIT-Domain Transpiler", description="Transpile MC domain and problem files to HDDL")
ARGPARSER.add_argument('--domain', '-d', type=str,
                    help='Path to the domain file')
ARGPARSER.add_argument('--problem', '-p', type=str,
                    help='Path to the problem file')
ARGPARSER.add_argument('--show-macro-result', '-m', action='store_true',
                    help='Show the intermediate result with applied macros')
ARGPARSER.add_argument('--out_domain', '-D', type=str, default="temp/domain.hddl",
                    help='Output path for the transpiled domain file')
ARGPARSER.add_argument('--out_problem', '-P', type=str, default="temp/problem.hddl",
                    help='Output path for the transpiled problem file')

def prepare_domain(domain_path: str, *, show_macro_result: bool = False, prec_replacement: bool = True) -> DomainFile:
    print("\n>> Transpiling Domain...")
    print("---------------------")
    domain = transpile_domain(
        domain_path,
        macro_funs=DOMAIN_MACRO_FUNS,
        show_macro_result=show_macro_result)

    if prec_replacement:
        domain_do_precondition_replacement(domain)
    return domain

def prepare_problem(problem_path: str, show_macro_result: bool = False) -> ProblemFile:
    print("\n>> Transpiling Problem...")
    print("----------------------")
    problem = transpile_problem(
        problem_path,
        macro_funs=PROBLEM_MACRO_FUNS,
        show_macro_result=show_macro_result)

    return problem

def main():
    args = ARGPARSER.parse_args()
    macros = args.show_macro_result

    if not args.domain and not args.problem:
        ARGPARSER.print_help()
        exit(1)

    if args.domain:
        domain = prepare_domain(args.domain, macros, show_macro_result=True)
        domain.write_to_file(args.out_domain)

    if args.problem:
        problem = prepare_problem(args.problem, macros)
        problem.write_to_file(args.out_problem)


if __name__ == "__main__":
    main()
