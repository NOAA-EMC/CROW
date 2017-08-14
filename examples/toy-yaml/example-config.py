#! /usr/bin/env python3.6

## Simple test program for crow.config module

import crow.config

config=crow.config.from_file('test.yml')

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
print("test_things.expandme = abc, def, ghi = "+
      repr(config.test_things.expandme))
