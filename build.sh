#!/bin/bash

git submodule update --init --recursive

cd panda/pandaPIparser
make -j
cd ../..

cd panda/pandaPIgrounder
cd cpddl
git apply ../0002-makefile.patch
make boruvka opts bliss lpsolve
make
cd ../src
make
cd ../../..

cd panda/pandaPIengine
mkdir build
cd build
cmake ../src
make -j
cd ../../..
