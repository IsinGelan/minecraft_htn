from typing import Iterator

from shit_transpiler import transpile_domain, transpile_problem
from shit_transpiler.helpers import Insertion, func_and, multi_insert
from shit_transpiler.shit_objs import Action, DomainFile, IdentifierParam, Method, SequencedSubtasks, ShitObject, FactExpr, ShitPredicate, SubtasksWithOrdering, Task, TaskCall, TopLevelComment
from shit_transpiler.paths import filter_parent_is, find_of_type, path_parent

from tools.get_names import get_block_names, get_item_names
from tools.generate_facts import generate
from tools.helpers import into_bins

MACRO_CONSTS_MARKER = "# MACRO CONSTS"
MACRO_FACTS_MARKER = "# MACRO FACTS"
BLOCK_TYPENAME = "Block"
ITEM_TYPENAME = "Item"
CONST_LINEWIDTH = 70

# ================================
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
    if line_start_index >= text_len:
        return
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
OPEN_PRECONDITION_PREDICATES = {
    "near_block": None,#"reach-block",
    "near_entity": (),#"reach-entity",
    "near_structure": (),#"reach-structure",
    "near_container_containing": (),#"reach-block",
    "has_item": (),#"acquire-item",
}

def fact_finder(pred_name: str):
    def wrapper_pred(node: ShitObject, _path: str):
        return isinstance(node, FactExpr) and node.predicate_name == pred_name
    return wrapper_pred

def prec_action_name(prec_pred: str) -> str:
    return f"fulfill-{prec_pred.replace('_', '-')}"

def args_from_params(params):
    return [IdentifierParam(name=param.name) for param in params]


# ================================
def domain_add_prec_actions(domain: DomainFile):
    # add actions that fulfill the open preconditions
    domain.top_level_elements.append(TopLevelComment(comment="PRECONDITION ACTIONS"))
    for prec_pred in OPEN_PRECONDITION_PREDICATES:
        pred_declaration, _ = next(
            find_of_type(domain, ShitPredicate, max_depth=None, extra_filter=lambda n, _: n.name == prec_pred))
        pred_declaration: ShitPredicate
        signature = pred_declaration.params
        action_name = f"fulfill-{prec_pred.replace('_', '-')}"
        postcondition = FactExpr(predicate_name=prec_pred, args=args_from_params(signature))
        action = Action(
            action_name=action_name,
            params=signature,
            precondition=[],
            postcondition=[postcondition])
        domain.top_level_elements.append(action)


def method_add_prec_action_calls(method: Method, pred_fact: FactExpr, prec_pred: str):
    prec_action_call = TaskCall(
        task_name=prec_action_name(prec_pred),
        args=pred_fact.args)
    if isinstance(method.subtasks, SequencedSubtasks):
        method.subtasks.subtasks.insert(0, prec_action_call)
    else:
        # method.subtasks: SubtasksWithOrdering
        subtask_indices = set(method.subtasks.subtasks.keys())
        new_index = max(subtask_indices, default=-1) + 1
        method.subtasks.subtasks |= {new_index: prec_action_call}
        # order it before all other subtasks
        ordering = [set(new_index), subtask_indices]
        method.subtasks.orderings.append(ordering)

def action_create_proxy_method(proxy_methods: dict[str, Method], action: Action, fact: FactExpr, prec_pred: str):
    action_params = action.params
    proxy_task_name = f"proxy-{action.action_name}"

    if proxy_task_name not in proxy_methods:
        method = Method(
            task_name=proxy_task_name,
            method_name="proxy",
            params=action_params,
            precondition=[],
            subtasks=SequencedSubtasks(subtasks=[
                TaskCall(
                    task_name=action.action_name,
                    args=args_from_params(action_params)
                )
            ])
        )
        method._set_task_params(method.params)
        proxy_methods[proxy_task_name] = method
    
    proxy_methods[proxy_task_name].subtasks.subtasks.insert(0, TaskCall(
        task_name=prec_action_name(prec_pred),
        args=fact.args
    ))

def prec_facts_of_type(
        prec_pred: str,
        in_class: type[ShitObject],
        domain: DomainFile) -> Iterator[tuple[FactExpr, str]]:
    return domain.traverse(
            func_and(
                filter_parent_is(
                    lambda parent, _: isinstance(parent, in_class),
                    lambda parent, child: child in parent.precondition),
                fact_finder(prec_pred),
            )
        )

def domain_add_prec_action_calls(domain: DomainFile):
    proxy_methods: dict[str, Method] = {}

    for prec_pred in OPEN_PRECONDITION_PREDICATES:
        # 1. find all occurrences in the domain
        # of facts of the predicate `prec_pred` (as preconditions)
        # 2. find methods / actions with precondition
        fact_occurrences = prec_facts_of_type(prec_pred, Method, domain)
        methods = {
            (parent:=node._origin.parent).full_name() : (parent, node)
            for node, _ in fact_occurrences
            }
        fact_occurrences = prec_facts_of_type(prec_pred, Action, domain)
        actions = {
            (parent:=node._origin.parent).action_name : (parent, node)
            for node, _ in fact_occurrences
            }

        # 3. For methods:
        # 3.1. add precondition action as first subtask
        for method, fact in methods.values():
            method_add_prec_action_calls(method, fact, prec_pred)

        # 4. For actions:
        # 4.1. make proxy task proxy-action = precondition action, then action call
        for action, fact in actions.values():
            action_create_proxy_method(proxy_methods, action, fact, prec_pred)

    domain.top_level_elements.append(TopLevelComment(comment="PROXY TASKS"))
    for _, proxy_method in proxy_methods.items():
        # 4.2. replace all action calls by proxy task calls
        action_name = proxy_method.task_name.removeprefix("proxy-")
        action_calls = domain.traverse(
            lambda node, _: isinstance(node, TaskCall) and node.task_name == action_name,
        )
        for action_call, _ in action_calls:
            action_call.task_name = proxy_method.task_name
        # 4.3. Add proxy method and task to domain
        # this way around to not replace the action call in the proxy
        task = Task(task_name=proxy_method.task_name, params=proxy_method.params)
        domain.top_level_elements.append(task)
        domain.top_level_elements.append(proxy_method)


# ================================
def main():
    domain = transpile_domain(
        "domain.shit",
        macro_funs=DOMAIN_MACRO_FUNS,
        show_macro_result=False)
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
