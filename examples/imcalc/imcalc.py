#! /usr/bin/env python3.6

## Unit test program for crow.config module

import sys, os, shutil, collections, copy

sys.path.append(os.getcwd() + '/../../')

import logging
from datetime import timedelta
from crow.config import from_dir, Suite, from_file, to_yaml, evaluate_immediates

platdoc=from_file('_common.yaml','_sandbox.yaml')
platdoc.platform.Evaluate=True
evaluate_immediates(platdoc.platform)

shutil.copyfile('resources_sum_sample.yaml','resources_sum.yaml')
doc=from_file('_common.yaml','_sandbox.yaml','case.yaml','default_resources.yaml','resources_sum.yaml')

filename = 'resources_sum.yaml'
rc_config = doc['partition_common']['resources']

def to_py(o,memo=None):
    if memo is None: memo=dict()
    i=id(o)
    if i in memo: return memo[i]
    if isinstance(o,bytes) or isinstance(o,str):
        ret=copy.copy(o)
        memo[i]=ret
    elif isinstance(o,collections.abc.Mapping):
        ret=dict()
        memo[i]=ret
        for k,v in o.items():
            py_k=to_py(k,memo)
            py_v=to_py(v,memo)
            ret[py_k]=py_v
    elif isinstance(o,collections.abc.Sequence):
        ret=list()
        memo[i]=ret
        for v in o:
            py_v=to_py(v,memo)
            ret.extend(py_v)
    else:
        ret=copy.copy(o)
        memo[i]=ret
    return ret

py_config=to_py(rc_config)
content = to_yaml(py_config)
with open(filename,'wt') as fd:
     fd.write(content)
resource_sum = from_file(filename)
value = { 'resources_sum': resource_sum }
content = to_yaml(value)
with open(filename,'wt') as fd:
     fd.write(content)

logging.basicConfig(stream=sys.stderr,level=logging.DEBUG)
