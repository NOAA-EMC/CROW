#! /usr/bin/env python3.6

import sys, os
import crow.config
import crow.metascheduler

run_dir=sys.argv[1]
config_yaml=os.path.join(run_dir,'config.yaml')
conf=crow.config.from_file(config_yaml)
suite=conf.workflow


print(repr(suite.Rocoto.scheduler))

rocoto_xml=crow.metascheduler.to_rocoto(suite)

print(rocoto_xml)
