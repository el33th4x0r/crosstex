#! /usr/bin/python3

import os
from subprocess import call, DEVNULL

DIR = "tests"

for filename in os.listdir(DIR):
    if not filename.endswith(".tex"):
        continue

    filename = filename.replace(".tex", "")
    path = DIR + "/" + filename

    print("### Running " + path)

    call(["xelatex", "--halt-on-error", filename], cwd=DIR, stdout=DEVNULL)
    call(["crosstex", filename], cwd=DIR)
    

