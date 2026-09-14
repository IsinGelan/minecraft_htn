.venv/bin/python compile.py --domain domain.shit --problem problem.shit
./panda/pandaPIparser/pandaPIparser domain.hddl problem.hddl res.htn
./panda/pandaPIgrounder/pandaPIgrounder res.htn res.sas
./panda/pandaPIengine/build/pandaPIengine res.sas