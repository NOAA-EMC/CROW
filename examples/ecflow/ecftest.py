#! /usr/bin/env python3
f'This script requires Python 3.6 or newer.'

from crow.metascheduler import to_ecflow
from crow.config import from_file, Suite

conf=from_file('ecftest.yaml')
suite=Suite(conf.suite)
print(f'Parent of suite.family2 is {suite.family2.up} = {suite.family2.up.path}')
suite_defs, ecf_files = to_ecflow(suite)

for defname in suite_defs:
    print(f'=== contents of suite def {defname}\n{suite_defs[defname]}')

for setname in ecf_files:
    print(f'ecf file set {setname}:\n')
    for filename in ecf_files[setname]:
        print(f'  file {filename}')
        for line in ecf_files[setname][filename].splitlines():
            print(f'    {line.rstrip()}')

