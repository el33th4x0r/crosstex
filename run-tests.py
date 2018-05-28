#! /usr/bin/python3

import os
import os.path
from sys import exit, argv 
from subprocess import call, DEVNULL

DIR = "tests"
num_tests = 0
success = 0
failure = 0

def run_test(path, filename):
    global num_tests
    global success
    global failure
    
    print("### Running " + path)

    # Run test
    call(["xelatex", "--halt-on-error", filename], cwd=DIR, stdout=DEVNULL)
    res = call(["crosstex" , "-v", filename], cwd=DIR)

    num_tests += 1

    if res == 0:
        success += 1
    else:
        failure += 1

    # Cleanup
    call(["rm", "-f", "*.cache", filename + ".pdf", filename + ".log", filename + ".aux"], cwd=DIR)


def run_all_tests():
    for filename in os.listdir(DIR):
        if not filename.endswith(".tex"):
            continue

        filename = filename.replace(".tex", "")
        path = DIR + "/" + filename
        run_test(path, filename)

if len(argv) < 2 or argv[1] == "all":
    run_all_tests()
else:
    name = argv[1]

    if not os.path.isfile(DIR + "/" + name + ".tex"):
        print("No such test " + name)
    else:
        run_test(DIR + "/" + name, name)

print("")
print(str(success) + "/" + str(num_tests) + " tests successful")
print(str(failure) + "/" + str(num_tests) + " tests failed")

if failure == 0:
    exit(0)
else:
    exit(-1)
    

