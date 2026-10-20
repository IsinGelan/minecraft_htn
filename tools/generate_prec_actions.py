
from typing import Iterator, Literal

from shitlang.helpers import func_and
from shitlang.shit_objs import (
    Action,
    DomainFile,
    IdentifierConst,
    IdentifierParam,
    Method,
    SequencedSubtasks,
    ShitObject,
    FactExpr,
    ShitPredicate,
    Task,
    TaskCall,
    TopLevelComment)
from shitlang.paths import find_of_type

# ================================
# Expansion modes: Ways to deal with open preconditions
# "none": do nothing, leave the precondition open
# "fulfill": insert a precondition action (resolvent) that fulfills the precondition
# "expand": insert an action call to a task that fulfills the precondition
# "expand" is a tuple of (precondition args, resolvent executable name, resolvent args)
Expansion = tuple[tuple[str, ...], str, tuple[str, ...]]
Replacement = Literal["none", "fulfill"] | Expansion

OPEN_PRECONDITION_PREDICATES: dict[str, Replacement] = {
    "near_block": (("b",), "reach-block", ("b",)), # "none", 
    "near_structure": (("s",), "reach-structure", ("s",)),
    "near_entity": (("e",), "find-entity", ("e",)),
    # "near_container_containing": (("c", "i"), "reach-container-containing", ("c", "i")),
    "has_item": (("i",), "acquire-item", ("i",)), # "fulfill"
}

# ================================
def _args_to_mapping(pred_args: tuple[str, ...], action_args: tuple[str, ...]) -> list[str | int]:
    return [
        pred_args.index(arg) if arg in pred_args else arg
        for arg in action_args]
def _fact_n_mapping_to_args(fact: FactExpr, mapping: list[str | int]) -> list[ShitObject]:
    return [
        fact.args[arg] if isinstance(arg, int) else IdentifierConst(name=arg)
        for arg in mapping]
PREC_CALL_ARG_MAPPING: dict[str, tuple[str | int, ...]] = {
    name: _args_to_mapping(args[0], args[2])
    for name, args in OPEN_PRECONDITION_PREDICATES.items()
    if isinstance(args, tuple)
}

def fact_needs_replacement(fact: FactExpr) -> bool:
    return (
        fact.predicate_name in OPEN_PRECONDITION_PREDICATES
        and OPEN_PRECONDITION_PREDICATES[fact.predicate_name] != "none")

# ================================
def fact_finder(pred_name: str):
    def wrapper_pred(node: ShitObject, _path: str):
        return isinstance(node, FactExpr) and node.predicate_name == pred_name
    return wrapper_pred

def prec_task_name(prec_pred: str) -> str:
    if prec_pred not in OPEN_PRECONDITION_PREDICATES:
        raise ValueError(f"Precondition predicate {prec_pred} not in OPEN_PRECONDITION_PREDICATES")
    if OPEN_PRECONDITION_PREDICATES[prec_pred] == "none":
        raise ValueError(f"Precondition predicate {prec_pred} has no action to fulfill it")
    if OPEN_PRECONDITION_PREDICATES[prec_pred] == "fulfill":
        return f"fulfill-{prec_pred.replace('_', '-')}"
    return OPEN_PRECONDITION_PREDICATES[prec_pred][1]

def fact_to_prec_task_call(fact: FactExpr) -> TaskCall:
    """Get the call replacing a precondition fact."""
    pred = fact.predicate_name
    task_name = prec_task_name(pred)
    if pred not in PREC_CALL_ARG_MAPPING:
        return TaskCall(task_name=task_name, args=fact.args)
    
    mapping = PREC_CALL_ARG_MAPPING[pred]
    args = _fact_n_mapping_to_args(fact, mapping)
    return TaskCall(task_name=task_name, args=args)

def args_from_params(params):
    return [IdentifierParam(name=param.name) for param in params]


# ================================
def domain_add_fulfill_actions(domain: DomainFile):
    """add actions that direcly assert a fact.
    Fulfillment actions have the same parameters as their corresponding predicate."""

    domain.top_level_elements.append(TopLevelComment(comment="PRECONDITION ACTIONS"))

    for prec_pred, resolution in OPEN_PRECONDITION_PREDICATES.items():
        if resolution == "none":
            continue
        if isinstance(resolution, tuple):
            continue

        pred_declaration, _ = next(
            find_of_type(domain, ShitPredicate, max_depth=None, extra_filter=lambda n, _: n.name == prec_pred))
        pred_declaration: ShitPredicate
        signature = pred_declaration.params
        task_name = f"fulfill-{prec_pred.replace('_', '-')}"
        postcondition = FactExpr(predicate_name=prec_pred, args=args_from_params(signature))
        action = Action(
            action_name=task_name,
            params=signature,
            precondition=[],
            postcondition=[postcondition])
        domain.top_level_elements.append(action)

# Methods should not receive added precondition calls,
# as their preconditions don't facilitate the assertion of facts necessary for execution
# but instead are used for method selection

# def method_add_prec_action_calls(method: Method, pred_fact: FactExpr, prec_pred: str):
#     prec_action_call = fact_to_prec_action_call(pred_fact, prec_pred)
#     if isinstance(method.subtasks, SequencedSubtasks):
#         method.subtasks.subtasks.insert(0, prec_action_call)
#     else:
#         # method.subtasks: SubtasksWithOrdering
#         subtask_indices = set(method.subtasks.subtasks.keys())
#         new_index = max(subtask_indices, default=-1) + 1
#         method.subtasks.subtasks |= {new_index: prec_action_call}
#         # order it before all other subtasks
#         ordering = [set(new_index), subtask_indices]
#         method.subtasks.orderings.append(ordering)

def proxy_method(
        action: Action,
        replace_facts: list[FactExpr]):
    """Add a precondition action call (fulfilling `fact`) to the proxy method for `action`.
    If the proxy method does not exist, create it.
    """
    action_params = action.params
    proxy_task_name = f"proxy-{action.action_name}"

    subtasks = SequencedSubtasks(
        subtasks=[fact_to_prec_task_call(fact) for fact in replace_facts]
        + [TaskCall(task_name=action.action_name, args=args_from_params(action_params))]
        )

    method = Method(
        task_name=proxy_task_name,
        method_name="proxy",
        params=action_params,
        precondition=[],
        subtasks=subtasks
    )
    method._set_task_params(method.params)
    return method

def action_proxy_methods(domain: DomainFile) -> Iterator[Method]:
    action_decls = (node for node in domain.top_level_elements if isinstance(node, Action))
    for action in action_decls:
        prec_facts = (expr for expr in action.precondition if isinstance(expr, FactExpr))
        replaced_prec_facts = [fact for fact in prec_facts if fact_needs_replacement(fact)]
        if not replaced_prec_facts:
            continue

        proxy = proxy_method(action, replaced_prec_facts)
        yield proxy

def domain_add_proxy_tasks(domain: DomainFile, proxy_methods: list[Method]):
    """Adding proxy methods to the domain and replacing action calls with proxy calls."""
    domain.top_level_elements.append(TopLevelComment(comment="PROXY TASKS"))
    for proxy_method in proxy_methods:
        # Info
        print(f"Adding proxy task {proxy_method.task_name!r}")

        # replace all action calls by proxy task calls
        action_name = proxy_method.task_name.removeprefix("proxy-")
        action_calls = domain.traverse(
            lambda node, _: isinstance(node, TaskCall) and node.task_name == action_name,
        )
        for action_call, _ in action_calls:
            action_call.task_name = proxy_method.task_name

        # add proxy method and task to domain
        task = Task(task_name=proxy_method.task_name, params=proxy_method.params)
        domain.top_level_elements.append(task)
        domain.top_level_elements.append(proxy_method)

def domain_do_precondition_replacement(domain: DomainFile):
    """Asserts that actions with certain precondition facts can always be executed.\n
    This is  done by creating an intermediate proxy method that calls the action and is called instead of it.\n
    The proxy method first calls all precondition actions/tasks to fulfill the action's precondition."""
    # 1. Add precondition actions to domain
    domain_add_fulfill_actions(domain)
    # 2. Create proxy methods for actions with preconditions that need replacement
    proxy_methods = list(action_proxy_methods(domain))
    # 3. Add proxy methods and tasks to domain, replacing action calls with proxy calls
    domain_add_proxy_tasks(domain, proxy_methods)
    # reinitialize model after adding new elements
    domain.model_post_init(None)
    