#!/bin/bash

transpile_domain=true
transpile_problem=true

while [ ! $# -eq 0 ]; do
    case "$1" in
        --keep-domain) transpile_domain=false ;;
        --keep-problem) transpile_problem=false ;;
        *)
            echo "Unknown option: $1" ;
            echo "Usage: $0 [--keep-domain] [--keep-problem]" ;
            exit 1 ;;
    esac
    shift
done

if $transpile_domain && $transpile_problem; then
    .venv/bin/python compile.py --domain domain.shit --problem problem.shit
elif $transpile_domain; then
    .venv/bin/python compile.py --domain domain.shit
elif $transpile_problem; then
    .venv/bin/python compile.py --problem problem.shit
fi

./panda/pandaPIparser/pandaPIparser temp/domain.hddl temp/problem.hddl temp/res.htn
./panda/pandaPIgrounder/pandaPIgrounder temp/res.htn temp/res.sas
./panda/pandaPIengine/build/pandaPIengine temp/res.sas