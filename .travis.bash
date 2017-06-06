#!/bin/bash -e
echo "underworlds CI setup and test"
echo "============================="
lsb_release -a; uname -a


UWDS_PREFIX=~/underworlds_install

mkdir -p ${UWDS_PREFIX}

echo "Build and install underwords"
python setup.py install --prefix=${UWDS_PREFIX}

export PATH=${PATH}:${UWDS_PREFIX}/bin
export PYTHONPATH=${UWDS_PREFIX}/lib/python2.7/site-packages:$PYTHONPATH

echo "Run tests"
cd testing
xvfb-run --auto-servernum --server-args="-screen 0 160x120x16" python2 ./run_tests.py

