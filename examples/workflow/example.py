#! /usr/bin/env python3.6

import sys
from datetime import timedelta
import crow.config
import crow.metascheduler

config=crow.config.from_file(
    'platform.yml','templates.yml','actions.yml','workflow.yml')

print(crow.metascheduler.to_rocoto(config.my_fancy_workflow))
