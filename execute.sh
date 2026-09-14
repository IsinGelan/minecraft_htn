#!/bin/bash

.venv/bin/python compile.py --domain domain.shit --problem problem.shit
./panda/pandaPIparser/pandaPIparser temp/domain.hddl temp/problem.hddl temp/res.htn
./panda/pandaPIgrounder/pandaPIgrounder temp/res.htn temp/res.sas
./panda/pandaPIengine/build/pandaPIengine temp/res.sas