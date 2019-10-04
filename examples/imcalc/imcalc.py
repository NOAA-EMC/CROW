#! /usr/bin/env python3.6

## Unit test program for crow.config module

import sys, os, shutil, collections, copy

sys.path.append(os.getcwd() + '/../../')

import logging
from datetime import timedelta
from crow.config import from_dir, Suite, from_file, to_yaml, evaluate_immediates, from_string
import crow.config.represent

from crow.config.eval_tools import list_eval, dict_eval
from crow.sysenv import JobResourceSpec

platdoc=from_file('_common.yaml','_sandbox.yaml')
platdoc.platform.Evaluate=True
evaluate_immediates(platdoc.platform)

shutil.copyfile('resources_sum_sample.yaml','resources_sum.yaml')
doc=from_file('_common.yaml','_sandbox.yaml','case.yaml','default_resources.yaml','resources_sum.yaml')

filename = 'resources_sum.yaml'

doc.writeme = { 'resources_sum': doc.partition_common.resources }
content = to_yaml({ 'resources_sum': doc.partition_common.resources })
with open(filename,'wt') as fd:
     fd.write(content)

logging.basicConfig(stream=sys.stderr,level=logging.DEBUG)
