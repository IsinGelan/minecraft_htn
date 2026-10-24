
from functools import reduce
from math import ceil
import re
from typing import Any, NamedTuple, Self

from shitlang.shit_objs import Action, FactExpr, Identifier, IdentifierParam, TaskCall, DomainFile, IdentifierConst
from tools.helpers import shared_keys, subdict, subdict_without

ITEM_PRED_NAME = "has_item"
NUMBERING_ANNOTATION_PATTERN = r"((,|^)\s*([\w\d_-]+\s+\d+))*\s*->\s*(\s*([\w\d_-]+\s+\d+)(,|$))*"
NUMBERING_ANNOTATION = re.compile(NUMBERING_ANNOTATION_PATTERN)
# EXAMPLE ANNOTATION = "apple 1, banana 13 -> bob 4, has_item 4"

class ActionNumbering(NamedTuple):
    action: Action
    input: dict[Identifier, int]
    output: dict[Identifier, int]

    def fix_params(self, action_call: TaskCall) -> Self:
        """Fixes the parameters using the task call"""
        assert action_call.task_name == self.action.action_name

        param_map = {p.name: a for p, a in zip(self.action.params, action_call.args)}
        fixed_input = {
            (param_map.get(k.name) if isinstance(k, IdentifierParam) else k) : v
            for k, v in self.input.items()}
        fixed_output = {
            (param_map.get(k.name) if isinstance(k, IdentifierParam) else k) : v
            for k, v in self.output.items()}
        if None in fixed_input or None in fixed_output:
            raise ValueError(f"ActionNumbering.fix_params: Some identifiers could not be matched "
                             f"to parameters in action call {action_call}")
        return ActionNumbering(self.action, fixed_input, fixed_output)

def has_action_item_pred(action: Action) -> bool:
    """Checks if the action has a precondition or postcondition with the predicate 'has_item'"""
    for fact in action.precondition + action.postcondition:
        if isinstance(fact, FactExpr) and fact.predicate_name == ITEM_PRED_NAME:
            return True
    return False

def parse_numbering_annotation(action: Action) -> ActionNumbering | None:
    """Parses the numbering annotation and returns a dictionary of input and output items with their counts"""
    annotation = action.annotation.strip() if action.annotation else ""
    if not NUMBERING_ANNOTATION.match(annotation):
        return None
    
    input_items = {}
    output_items = {}

    input_part, output_part = annotation.split("->")
    for item_nr in input_part.split(","):
        if item_nr.strip() == "": continue
        item, nr = item_nr.strip().split()
        ide = IdentifierParam(name=item) if item in action.param_names else IdentifierConst(name=item)
        input_items[ide] = int(nr)
    for item_nr in output_part.split(","):
        if item_nr.strip() == "": continue
        item, nr = item_nr.strip().split()
        ide = IdentifierParam(name=item) if item in action.param_names else IdentifierConst(name=item)
        assert nr.isdecimal() and int(nr) >= 0, f"Invalid number in annotation output: {nr}"
        output_items[ide] = int(nr)

    return ActionNumbering(action, input_items, output_items)

def add_numbering_to_action(action: Action) -> int | None:
    """Adds an attribute for the numbers in the annotation"""
    if not action.annotation:
        if has_action_item_pred(action):
            print(f"Warning: Action '{action.action_name}' uses {ITEM_PRED_NAME} predicate but has no annotation.")
            pass
        return None
    
    numbering = parse_numbering_annotation(action)
    if numbering:
        action._item_numbering = numbering

def add_numbering_to_domain(domain: DomainFile):
    """Adds an attribute for the numbers in the annotation to all actions in the domain"""
    for action in domain.top_level_elements:
        if not isinstance(action, Action):
            continue
        add_numbering_to_action(action)

# ================================
def action_count_provides(action_numbering: ActionNumbering, resources: dict[Identifier, int]) -> int:
    """Returns how many times the action needs to be called to provide the resources"""
    return max(
        # How many times the action would need to be called for this resource
        ceil(count / action_numbering.output[resource])
        for resource, count in resources.items()
    )

def numbered_plan(plan: list[TaskCall], domain: DomainFile) -> list[tuple[TaskCall, int]]:
    """Compute how many times each annotated action needs to be called
    to satisfy the action numbering annotations"""
    print(">> Computing action repetitions for plan")
    get_action = lambda name: next(
        el for el in domain.top_level_elements
        if isinstance(el, Action) and el.action_name == name)
    
    # Numberings for task calls of numbered actions
    fixed_numberings: dict[TaskCall, ActionNumbering] = {
        tc: get_action(tc.task_name)._item_numbering.fix_params(tc)
        for tc in plan
        if hasattr(get_action(tc.task_name), "_item_numbering")
    }

    action_counts = {tc: 1 for tc in fixed_numberings.keys()}

    # Resources that are not yet provided by any TaskCall
    open_resources: dict[IdentifierConst, int] = {}
    # Find the number of times each action needs to be executed
    for tc in plan[::-1]:
        if tc not in fixed_numberings:
            continue
        numbering = fixed_numberings[tc]
        satisfies = shared_keys(open_resources, numbering.output)
        if satisfies:
            action_counts[tc] = action_count_provides(
                numbering, subdict(open_resources, satisfies))
            open_resources = subdict_without(open_resources, satisfies)
        for resource, count in numbering.input.items():
            open_resources[resource] = open_resources.get(resource, 0) + count * action_counts[tc]

    if open_resources:
        print("Warning: Some resources are not provided by any action in the plan:")
        for resource, count in open_resources.items():
            print(f"- {resource}: {count}")

    return [(tc, action_counts.get(tc, 1)) for tc in plan]
