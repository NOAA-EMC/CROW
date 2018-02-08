#! /usr/bin/env python3
f'This script requires Python 3.6 or newer.'

import os
from crow.metascheduler import to_rocoto
from crow.config import from_file, Suite

conf=from_file('resources.yaml','rocoto.yaml','suite_def.yaml','settings.yaml')
suite=Suite(conf.suite)
with open('workflow.xml','wt') as fd:
    print('workflow.xml')
    fd.write(to_rocoto(suite))
