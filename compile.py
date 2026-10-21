
import argparse

from shitlang import get_domain, get_problem, optimize_domain
from shitlang.main import DUMP_DOMAIN_PATH
from shitlang.shit_objs import DomainFile, ProblemFile

from tools.generate_crafting import get_recipe_names, recipes_string
from tools.generate_prec_actions import domain_do_precondition_replacement
from tools.get_names import get_block_names, get_entity_names, get_item_names
from tools.generate_facts import generate, get_block_tag_names, get_item_tag_names, get_structure_names
from tools.helpers import read_or_compute, split_into_lines
from tools.number_annotations import add_numbering_to_domain

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

FACTS_FILE_PATH = "domain_facts.pro"
CRAFTING_FILE_PATH = "recipes.shit"

# ================================
def typed_declarations(typename: str, names: list[str]) -> str:
    """Generate a string of const declarations for the given names and typename"""
    names_string = " ".join(sorted(names))
    lines = [
        f"const {line} : {typename}\n"
        for line in split_into_lines(names_string, CONST_LINEWIDTH)]
    return "".join(lines)

def add_consts(code: str) -> str:
    blocks_decls = typed_declarations(BLOCK_TYPENAME, get_block_names())
    items_decls = typed_declarations(ITEM_TYPENAME, set(get_item_names()))
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
    # recipes_str = recipes_string(numbered=False)
    recipes_str = read_or_compute(
        CRAFTING_FILE_PATH,
        read_fun=lambda s: s,
        compute_fun=lambda: recipes_string(numbered=False),
        write_fun=lambda s: s
    )
    return code.replace(MACRO_CRAFTING_MARKER, recipes_str)

def add_domain_facts(code: str) -> str:
    facts_string = read_or_compute(
        FACTS_FILE_PATH,
        read_fun=lambda s: s.replace(".", ""),
        compute_fun=lambda: "\n".join(generate()),
        write_fun=lambda s: s.replace("\n", ".\n") + ".\n")

    return code.replace(MACRO_FACTS_MARKER, facts_string)


DOMAIN_MACRO_FUNS = [
    add_consts,
    add_crafting_recipes,
]
PROBLEM_MACRO_FUNS = [
    add_domain_facts,
]

FALSE_PREDS = {
    "has_item", "can_reap_block", "can_reap_entity", "reaped_block_becomes",
    "near_container_containing", "reaped_entity_becomes", "near_item_entity"}

# ================================
def prepare_domain(
        domain_path: str, *,
        show_macro_result: bool = False,
        prec_replacement: bool = True,
        dump_json: bool = True,
        add_action_numbering: bool = True) -> DomainFile:
    """Transpile domain and do all domain-specific preprocessing.\n
    domain_path: Path to the domain file\n
    show_macro_result: If True, show the intermediate result with applied macros\n
    prec_replacement: If True, wrap actions in precondition-fulfilling proxy tasks\n
    dump_json: If True, dump the domain to a JSON file\n
    add_action_numbering: If True, add numbering to actions with numbering annotations"""

    print("\n>> Transpiling Domain...")
    print("---------------------")
    domain, recompiled = get_domain(
        domain_path,
        macro_funs=DOMAIN_MACRO_FUNS,
        show_macro_result=show_macro_result)

    if prec_replacement and recompiled:
        print(">> Replacing preconditions with precondition actions")
        domain_do_precondition_replacement(domain)
    if add_action_numbering:
        add_numbering_to_domain(domain)
    if dump_json:
        domain.dump_json(DUMP_DOMAIN_PATH)
    return domain

def prepare_problem(problem_path: str, show_macro_result: bool = False) -> ProblemFile:
    print("\n>> Transpiling Problem...")
    print("----------------------")
    problem = get_problem(
        problem_path,
        macro_funs=PROBLEM_MACRO_FUNS,
        show_macro_result=show_macro_result)

    return problem

# ================================
def main(
    in_domain: str = None,
    in_problem: str = None, *,
    out_domain: str = "temp/domain.hddl",
    out_problem: str = "temp/problem.hddl",
    show_macro_result: bool = False
    )-> tuple[DomainFile | None, ProblemFile | None, bool | None]:
    """Transpiles domain and problem files to HDDL files.
    If both are provided, the domain is optimized based on the problem.\n
    returns: (domain, problem, optimization_success)"""

    if in_domain and in_problem:
        print("Transpiling domain and problem and optimizing domain based on problem")
        domain = prepare_domain(in_domain, show_macro_result=show_macro_result)
        problem = prepare_problem(in_problem, show_macro_result=show_macro_result)
        opt_success = optimize_domain(domain, problem, recompile_pro_domain=True, false_preds=FALSE_PREDS)
        domain.export_hddl(out_domain)
        problem.export_hddl(out_problem)
        return (domain, problem, opt_success)

    if in_domain:
        domain = prepare_domain(in_domain, show_macro_result=show_macro_result)
        domain.export_hddl(out_domain)
        return (domain, None, None)

    if in_problem:
        problem = prepare_problem(in_problem, show_macro_result=show_macro_result)
        problem.export_hddl(out_problem)
        return (None, problem, None)

    return (None, None, None)

ARGPARSER = argparse.ArgumentParser(
    prog="Minecraft SHIT-Domain Transpiler",
    description="Transpile MC domain and problem files to HDDL")
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

def cmd_main():
    args = ARGPARSER.parse_args()

    if not args.domain and not args.problem:
        ARGPARSER.print_help()
        exit(1)

    main(
        in_domain=args.domain,
        in_problem=args.problem,
        out_domain=args.out_domain,
        out_problem=args.out_problem,
        show_macro_result=args.show_macro_result
    )

if __name__ == "__main__":
    cmd_main()
