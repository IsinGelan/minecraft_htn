
import subprocess

from compile import main as compile_main
from shitlang.shit_objs import IdentifierConst, TaskCall
from tools.number_annotations import numbered_plan

IN_DOMAIN = "domain.shit"
IN_PROBLEM = "problem.shit"

COMMAND_PARSER = "./panda/pandaPIparser/pandaPIparser temp/domain.hddl temp/problem.hddl temp/res.htn"
COMMAND_GROUNDER = "./panda/pandaPIgrounder/pandaPIgrounder temp/res.htn temp/res.sas"
COMMAND_ENGINE = "./panda/pandaPIengine/build/pandaPIengine temp/res.sas"

# ================================
def parse_call_line(line: str, exclude_tasks: set[str] = {"dono"}) -> TaskCall | None:
    """Parses a line from the planner output and returns a TaskCall object"""
    line = line.strip()
    index, call = line.split(" ", 1)
    body_start = call.find("[")
    body_end = call.rfind("]")
    assert body_start != -1
    assert body_end != -1

    task_name = call[:body_start]
    if task_name in exclude_tasks:
        return None
    if task_name.startswith("__"):
        # Ignore method precondition tasks from PANDA
        return None
    
    body = call[body_start+1:body_end]
    args = [IdentifierConst(name=arg) for arg in body.split(",")] if body else []
    return TaskCall(task_name=task_name, args=args)

def extract_plan(planner_output: str, exclude_tasks: set[str] = {"dono"}) -> list[TaskCall] | None:
    """Extracts the plan from the planner output"""
    failed = "Proven unsolvable" in planner_output
    if failed:
        return None
    start = planner_output.find("==>\n") + 4
    end = planner_output.find("\nroot 0", start + 1)
    lines = planner_output[start:end].splitlines()

    return [call for line in lines if (call := parse_call_line(line, exclude_tasks)) is not None]

# ================================
def process_failure(process: subprocess.CompletedProcess, command: str):
    print("ERROR: Process failed with return code", process.returncode)
    print("Command:", command)
    print("------------------------------")
    print(process.stderr)

def main():
    domain, _, _ = compile_main(
        in_domain=IN_DOMAIN,
        in_problem=IN_PROBLEM
    )

    print("\n>> Running planner...")
    print("----------------------")
    process_parser = subprocess.run(COMMAND_PARSER,shell=True,capture_output=True,text=True)
    if process_parser.returncode != 0:
        return process_failure(process_parser, COMMAND_PARSER)
    process_grounder = subprocess.run(COMMAND_GROUNDER,shell=True,capture_output=True,text=True)
    if process_grounder.returncode != 0:
        return process_failure(process_grounder, COMMAND_GROUNDER)
    process_engine = subprocess.run(COMMAND_ENGINE,shell=True,capture_output=True,text=True)
    if process_engine.returncode != 0:
        return process_failure(process_engine, COMMAND_ENGINE)

    plan = extract_plan(process_engine.stdout)
    num_plan = numbered_plan(plan, domain)
    print(*(f"{num:>2}x {tc}" for tc, num in num_plan), sep='\n')

if __name__ == "__main__":
    main()