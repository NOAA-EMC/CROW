#! /usr/bin/env python3
f'This script requires Python 3.6 or newer.'

import os, sys

sys.path.append(os.getcwd() + '/../../')

from crow.metascheduler import to_ecflow
from crow.config import from_file, Suite

conf=from_file('ecftest.yaml')
suite=Suite(conf.suite)
ecflow_suite = to_ecflow(suite)

for defname in ecflow_suite.suite_defs_by_file:
    #print(f'=== contents of suite def {defname}\n{suite_defs[defname]}')
    filename=defname
    print(filename)
    dirname=os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(os.path.dirname(filename))
    with open(filename,'wt') as fd:
        fd.write(ecflow_suite.suite_defs_by_file[defname][1])

setname = ecflow_suite.ecf_file_set_paths['/']
print(f'ecf file set {setname}:\n')
for filename in ecflow_suite.ecf_files['/']:
    print(f'  file {filename}')
    dirname=os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(os.path.dirname(filename))
    with open(filename+".ecf",'wt') as fd:
        fd.write(ecflow_suite.ecf_files['/'][filename])
        
        #for line in ecf_files[setname][filename].splitlines():
            #print(f'    {line.rstrip()}')

