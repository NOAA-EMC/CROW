#! /usr/bin/env python3
f'This script requires Python 3.6 or newer.'

import os
from crow.metascheduler import to_ecflow
from crow.config import from_file, Suite

conf=from_file('resources.yaml', 'suite_def.yaml')
suite=Suite(conf.suite)
suite_defs, ecf_files = to_ecflow(suite)

def make_parent_dir(filename):
    dirname=os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(os.path.dirname(filename))

for deffile in suite_defs.keys():
    defname,defcontents = suite_defs[deffile]
    #print(f'=== contents of suite def {defname}\n{suite_defs[defname]}')
    filename=os.path.join('defs',deffile)
    make_parent_dir(filename)
    print(filename)
    dirname=os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(os.path.dirname(filename))
    with open(filename,'wt') as fd:
        fd.write(defcontents)

    for setname in ecf_files:
        print(f'ecf file set {setname}:\n')
        for filename in ecf_files[setname]:
            full_fn=os.path.join('scripts',defname,filename)+'.ecf'
            print(f'  file {full_fn}')
            make_parent_dir(full_fn)
            with open(full_fn,'wt') as fd:
                fd.write(ecf_files[setname][filename])

