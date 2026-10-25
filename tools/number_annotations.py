
from functools import reduce
from math import ceil
import re
from typing import Any, NamedTuple, Self

from pydantic import BaseModel

from shitlang.shit_objs import Action, FactExpr, Identifier, IdentifierParam, TaskCall, DomainFile, IdentifierConst
from tools.helpers import as_list, connected_components, find, is_consecutive, reverse_enumerated, shared_keys, subdict, subdict_without

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
# {ressource : [number, {consumers}]}
class CountAndConsumers(BaseModel):
    count: int
    consumers: set[int] 
    def __list__(self):
        return [self.count, self.consumers]
    def __iter__(self):
        return iter((self.count, self.consumers))
RessourceDict = dict[IdentifierConst, CountAndConsumers]



class NumberedPlan(BaseModel):
    calls_reps: list[tuple[TaskCall, int]]
    provider_consumer: set[tuple[int, int, IdentifierConst]]

    @property
    def call_ids(self) -> set[int]:
        return set(range(len(self.calls_reps)))

    def _grouped_plan(self, groups: list[set[int]]):
        """groups of task call groups of local resources"""
        grouped_plan: list[tuple[int, list[TaskCall]]] = []
        skip_until = -1
        for i, (call, count) in enumerate(self.calls_reps):
            if i <= skip_until:
                grouped_plan[-1][1].append(call)
                assert count == grouped_plan[-1][0]
            else:
                grouped_plan.append((count, [call]))
                group = find(groups, lambda gr: i in gr)
                assert group
                skip_until = max(group)
        return grouped_plan

    @as_list
    def expanded_plan(self, domain: DomainFile, local_resource_types: set[str]):
        """Expand the numbered plan into a concrete plan.\n
        local_ressource_types: Typenames for local ressources\n
        local ressources are those that cannot be acquired, so the consumer has to directly follow the provider"""
        # 1. Identify groups
        # Links providing local ressources
        local_resource_links = {
            (p_id, c_id)
            for p_id, c_id, res
            in self.provider_consumer if domain.type_of(res) in local_resource_types}
        groups = connected_components(self.call_ids, local_resource_links)
        assert all(is_consecutive(group) for group in groups)
        # 2. Group the plan
        grouped_plan = self._grouped_plan(groups)
        # 3. yield groups repeated 
        for count, group in grouped_plan:
            for _ in range(count):
                yield from group

# ================================
def action_count_provides(action_numbering: ActionNumbering, resources: RessourceDict) -> int:
    """Returns how many times the action needs to be called to provide the resources"""
    return max(
        # How many times the action would need to be called for this resource
        ceil(count / action_numbering.output[resource])
        for resource, (count, _) in resources.items()
    )

def numbered_plan(plan: list[TaskCall], domain: DomainFile) -> NumberedPlan:
    """Compute how many times each annotated action needs to be called
    to satisfy the action numbering annotations"""
    print(">> Computing action repetitions for plan")
    # Numberings for task calls of numbered actions
    # TODO: use task indices as keys 
    fixed_numberings: dict[TaskCall, ActionNumbering] = {
        tc: action._item_numbering.fix_params(tc)
        for tc in plan
        if hasattr(
            action := domain.get_tle(Action, tc.task_name),
            "_item_numbering")
    }

    # Repetitions for the calls
    call_reps = {tc: 1 for tc in fixed_numberings.keys()}
    # {(provider, consumer, ressource_name)}
    provider_consumer: set[tuple[int, int, IdentifierConst]] = set()
    # Resources that are not yet provided by any TaskCall
    open_resources: dict[IdentifierConst, CountAndConsumers] = {}

    # Find the number of times each action needs to be executed
    for call_index, tc in reverse_enumerated(plan):
        if tc not in fixed_numberings:
            # Actions without numbering annotations do not provide or consume
            continue

        numbering = fixed_numberings[tc]
        satisfies = shared_keys(open_resources, numbering.output)

        if satisfies:
            provided = subdict(open_resources, satisfies)
            # satisfied_consumers: set[int] = set.union(*(cc.consumers for cc in provided.values()))
            provider_consumer.update(
                (call_index, consumer_index, res)
                for res, cc in provided.items()
                for consumer_index in cc.consumers)
            call_reps[tc] = action_count_provides(numbering, provided)
            open_resources = subdict_without(open_resources, satisfies)
        
        for resource, count in numbering.input.items():
            if resource not in open_resources:
                open_resources[resource] = CountAndConsumers(count=0, consumers=set())
            open_resources[resource].count += count * call_reps[tc]
            open_resources[resource].consumers.add(call_index)

    if open_resources:
        print("Warning: Some resources are not provided by any action in the plan:")
        for resource, count in open_resources.items():
            print(f"- {resource}: {count}")

    return NumberedPlan(
        calls_reps=[(tc, call_reps.get(tc, 1)) for tc in plan],
        provider_consumer=provider_consumer
    )

# def expand_numbered_plan(
#         num_plan: list[tuple[TaskCall, int]],
#         domain: DomainFile,
#         local_ressource_types: list[str]) -> list[TaskCall]:
#     """Expand the numbered plan into a concrete plan with repeated actions.\n
#     local_ressource_types: Typenames for local ressources\n
#     local ressources are those that cannot be acquired, so the consumer has to directly follow the provider"""
