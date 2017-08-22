#! /usr/bin/env python3.6

## Simple test program for crow.config module

import sys
from datetime import timedelta
import crow.config
import crow.metascheduler

config=crow.config.from_file('test.yml')

print()
# suite=crow.config.Suite(config.my_fancy_workflow)
# for task in suite.walk_task_tree():
#     print(f"Task {task.path}")
#     for var in [ 'Trigger', 'Complete', 'Time' ]:
#         if var in task:
#             print(f'  + {var} = {task[var]}')
print()
print("test = expected value = actual value")
print()
print("gfsfcst.a = 10 = "+repr(config.gfsfcst.a))
print("gfsfcst.d = 9200 = "+repr(config.gfsfcst.d))
print("gfsfcst.stuff[0] = 30 = "+repr(config.gfsfcst.stuff[0]))
print("least utilized scrub area = "+repr(config.platform.scrub))
print("config.platform.B = 'B' = "+repr(config.platform.B))
print("config.platform.C = 'C' = "+repr(config.platform.C))
print("config.platform.none = None = "+repr(config.platform.none))
print()
for bad in ['lt','ft','xv','nv']:
    print( "config.platform['bad%s'] = None = %s"%(
        bad,config.platform['bad'+bad]))
print()
print("config.gfsfcst.cow = blue = "+repr(config.gfsfcst.cow))
print("config.gfsfcst.dog = brown = "+repr(config.gfsfcst.dog))
print("config.gfsfcst.lencow = 4 = "+repr(config.gfsfcst.lencow))
print()
print('config.test.dt = datetime.timedelta(0, 12000) = '+
      repr(config.test.dt))
print('config.test.fcsttime = datetime.datetime(2017, 9, 19, 21, 20) = '+
      repr(config.test.fcsttime))
print('config.test.fYMDH = 2017091921 = '+repr(config.test.fYMDH))
print()
print("config.test.expandme = abc, def, ghi = "+
      repr(config.test.expandme))
print('config.fcst.hydro_mono = hydro_mono = '+
      repr(config.fcst.hydro_mono))
print('config.fcst.some_namelist: \n'+str(config.fcst.some_namelist))

with open('namelist.nl','rt') as fd:
    namelist_nl=fd.read()

print('config.fcst.expand_text(...namelist.nl...): \n'+
      crow.config.expand_text(namelist_nl,config.fcst))
print()
crow.metascheduler.to_rocoto(config.my_fancy_workflow,sys.stdout)

