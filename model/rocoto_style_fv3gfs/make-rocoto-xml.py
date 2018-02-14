#! /usr/bin/env python3
f'This script requires Python 3.6 or newer.'

import os, io
from crow.metascheduler import to_rocoto
from crow.config import from_dir, Suite

conf=from_dir('.')
suite=Suite(conf.suite)
with open('workflow.xml','wt') as fd:
    print('workflow.xml')
    fd.write(to_rocoto(suite))
