#! /usr/bin/env python3
f'This script requires Python 3.6 or newer.'

import os, io, sys
from crow.metascheduler import to_ecflow
from crow.config import from_dir, Suite

if len(sys.argv) != 2:
    sys.stderr.write('Syntax: make-ecflow-suite.py PSLOT\n')
    sys.stderr.write('PSLOT must match what you gave setup_expt.py\n')
    sys.exit(1)

conf=from_dir('.')
conf.sys_argv_1=sys.argv[1]
suite=Suite(conf.suite)
suite_defs, ecf_files = to_ecflow(suite)

def make_parent_dir(filename):
    dirname=os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(os.path.dirname(filename))

for deffile in suite_defs.keys():
    defname = suite_defs[deffile]['name']
    defcontents = suite_defs[deffile]['def']
    #print(f'=== contents of suite def {defname}\n{suite_defs[defname]}')
    filename=os.path.join('defs',deffile)
    make_parent_dir(filename)
    with open(filename,'wt') as fd:
        fd.write(defcontents)

    for setname in ecf_files:
        print(f'ecf file set {setname}:')
        for filename in ecf_files[setname]:
            full_fn=os.path.join(defname,filename)+'.ecf'
            print(f'  file {full_fn}')
            make_parent_dir(full_fn)
            with open(full_fn,'wt') as fd:
                fd.write(ecf_files[setname][filename])

