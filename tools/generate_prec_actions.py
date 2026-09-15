
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
from shitlang.paths import filter_parent_is, find_of_type

# ================================
# Expansion modes: Ways to deal with open preconditions
# "none": do nothing, leave the precondition open
# "fulfill": insert a precondition action (resolvent) that fulfills the precondition
# "expand": insert an action call to a task that fulfills the precondition
# "expand" is a tuple of (precondition args, resolvent executable name, resolvent args)
Expansion = tuple[tuple[str, ...], str, tuple[str, ...]]
Resolution = Literal["none", "fulfill"] | Expansion

OPEN_PRECONDITION_PREDICATES: dict[str, Resolution] = {
    "near_block": "none", #"reach-block",
    "near_structure": (("s",), "reach-structure", ("s",)),
    "near_entity": (("e",), "find-entity", ("e",)),
    # "near_container_containing": (("c", "i"), "reach-container-containing", ("c", "i")),
    "has_item": "fulfill", #"acquire-item",
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

def fact_finder(pred_name: str):
    def wrapper_pred(node: ShitObject, _path: str):
        return isinstance(node, FactExpr) and node.predicate_name == pred_name
    return wrapper_pred

def prec_action_name(prec_pred: str) -> str:
    if prec_pred not in OPEN_PRECONDITION_PREDICATES:
        raise ValueError(f"Precondition predicate {prec_pred} not in OPEN_PRECONDITION_PREDICATES")
    if OPEN_PRECONDITION_PREDICATES[prec_pred] == "none":
        raise ValueError(f"Precondition predicate {prec_pred} has no action to fulfill it")
    if OPEN_PRECONDITION_PREDICATES[prec_pred] == "fulfill":
        return f"fulfill-{prec_pred.replace('_', '-')}"
    return OPEN_PRECONDITION_PREDICATES[prec_pred][1]

def fact_to_prec_action_call(fact: FactExpr, prec_pred: str) -> TaskCall:
    """Get the call replacing a precondition fact."""
    task_name = prec_action_name(prec_pred)
    if prec_pred not in PREC_CALL_ARG_MAPPING:
        return TaskCall(task_name=task_name, args=fact.args)
    
    mapping = PREC_CALL_ARG_MAPPING[prec_pred]
    args = _fact_n_mapping_to_args(fact, mapping)
    return TaskCall(task_name=task_name, args=args)

def args_from_params(params):
    return [IdentifierParam(name=param.name) for param in params]


# ================================
def domain_add_prec_actions(domain: DomainFile):
    # add actions that fulfill the open preconditions
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


def method_add_prec_action_calls(method: Method, pred_fact: FactExpr, prec_pred: str):
    prec_action_call = fact_to_prec_action_call(pred_fact, prec_pred)
    # prec_action_call = TaskCall(
    #     task_name=prec_action_name(prec_pred),
    #     args=pred_fact.args)
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

def action_create_proxy_method(
        proxy_methods: dict[str, Method],
        action: Action,
        fact: FactExpr,
        prec_pred: str):
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
    
    proxy_methods[proxy_task_name].subtasks.subtasks.insert(
        0, fact_to_prec_action_call(fact, prec_pred))

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

    for prec_pred, resolution in OPEN_PRECONDITION_PREDICATES.items():
        if resolution == "none":
            continue

        # check that the called action exists
        resolvent_name = prec_action_name(prec_pred)
        assert any(
            isinstance(node, Action) and node.action_name == resolvent_name
            or isinstance(node, Task) and node.task_name == resolvent_name
            for node in domain.top_level_elements), \
            f"Expected precondition executable {resolvent_name!r} " \
            f"for predicate {prec_pred!r} not found in domain"

        # Info
        print(f"Replacing precondtion for predicate {prec_pred!r} -> call {resolvent_name!r}")

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
        # Info
        print(f"Adding proxy task {proxy_method.task_name!r}")

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