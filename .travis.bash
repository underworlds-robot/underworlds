#!/bin/bash -e
echo "underworlds CI setup and test"
echo "============================="
lsb_release -a; uname -a

UWDS_CLONE_PATH=`pwd`
UWDS_PREFIX=~/underworlds_install
mkdir -p ${UWDS_PREFIX}


echo "Installing pyassimp"

# create this symbolic link otherwise pyassimp does not find libassimp
sudo ln -s /usr/lib/libassimp.so.3 /usr/lib/libassimp.so

cd ${HOME}
git clone --depth=1 https://github.com/assimp/assimp.git
cd assimp/port/PyAssimp

# workaround for bug introduced in assimp's 33bd5cfcfb0f27794a333273b20b60a7a550d184
mkdir ../../lib

python setup.py install --prefix=${UWDS_PREFIX}

echo "Build and install underwords"
cd ${UWDS_CLONE_PATH}


python setup.py install --prefix=${UWDS_PREFIX}

export PATH=${PATH}:${UWDS_PREFIX}/bin
export PYTHONPATH=${UWDS_PREFIX}/lib/python2.7/site-packages:$PYTHONPATH

echo "Run tests"
cd testing

# launch all tests, except OpenGL tests
python2 ./run_tests.py --nogl

