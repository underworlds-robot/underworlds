#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os
import logging
import time
import unittest
import getopt

import operator

def usage():
    print("""Unit-testing for the LAAS-CNRS 'underworlds' module.

Usage:
run_tests [OPTIONS]
  -h, --help               Displays this message and exits
  -f, --failfast           Stops at first failure or error
  --nogl                   Do not run tests requiring OpenGL support
  -l, --log=[file|stdout]  Where to log: file (in """ + LOG_FILENAME + """) 
                           or stdout (default).
""")


LOG_FILENAME = "underworlds_tests.log"

#Set the loggers
logger = logging.getLogger('underworlds')
logger.setLevel(logging.DEBUG)

log_handler = logging.StreamHandler()
formatter = logging.Formatter("%(message)s")

failfast = False
nogl = False

try:
    optlist, args = getopt.getopt(sys.argv[1:], 'hfl:', ['help', 'failfast', 'log=', 'nogl'])
except getopt.GetoptError as err:
    # print help information and exit:
    print(str(err)) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

for o, a in optlist:
    if o in ("-h", "--help"):
        usage()
        sys.exit(0)
    if o in ("-f", "--failfast"):
        print("Failfast mode enabled.")
        failfast = True
    elif o == "--nogl":
        print("Running without OpenGL support.")
        nogl = True
    elif o in ("-l", "--log"):
        if a == "file":
            print(("The output of the unit-tests will be saved in " + LOG_FILENAME))
            log_handler = logging.FileHandler(LOG_FILENAME)
    else:
        print("Unhandled option " + o)
        usage()
        sys.exit(2)

# add formatter to log_handler
log_handler.setFormatter(formatter)
# add log_handler to logger
logger.addHandler(log_handler)



def getTestRunner(failsafe, verbosity = 2):
    if sys.version_info >= (2,7,0):
        return unittest.TextTestRunner(verbosity=2, failfast = failfast)
    else:
        if failsafe:
            print ("Running Python < 2.7. Failsafe mode not possible.")
        #failsafe not handled
        return unittest.TextTestRunner(verbosity=2)

results = {}

def runtest(module):
    suite = module.test_suite()
    result = getTestRunner(failfast).run(suite)

    results[module.__name__] = (suite.countTestCases(), result.testsRun, len(result.failures) , len(result.errors), result.testsRun - len(result.failures) - len(result.errors))

    time.sleep(0.5)

    return result.wasSuccessful()

########################################################################
########################################################################

#Import unit-tests
import basic_server_interaction, \
       topology, \
       core, \
       nodes, \
       waitforchanges, \
       timeline, \
       model_loading

modules = [
    basic_server_interaction, \
    topology, \
    core, \
    nodes, \
    waitforchanges, \
    timeline, \
    model_loading]

# add the tests which require OpenGL support
if not nogl:
    import visibility
    modules += [visibility]


for m in modules:
    print("\n****************************************************\nRunning tests in <%s>...\n" % m.__name__)
    ok = runtest(m)
    if failfast and not ok:
        break

########################################################################
########################################################################

total = (0,0,0,0,0)
total_ok = 0
print("\n\n==============================================================================")
print("| suite                    | nb tests | tests run | failures | errors ||  OK |")
print("|----------------------------------------------------------------------------|")
for name in results:
    total = list(map(operator.add, total, results[name]))
    print((  "| " + name + (" "* (25 - len(name))) + \
            "|   % 3d    |    % 3d    |   % 3d    |  % 3d   || % 3d |" % (results[name])))
    print("|----------------------------------------------------------------------------|")
    
print(("| TOTAL                    |  % 4d    |   % 4d    |   % 3d    |  % 3d   || % 3d |" % (tuple(total))))
print("==============================================================================")

sys.exit(0 if total[1] == total[4] else 1)
