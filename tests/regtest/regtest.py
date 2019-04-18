#!/usr/bin/env python3

import logging, os, io, sys, datetime, glob, shutil, subprocess, re, itertools, collections
from collections import OrderedDict
from copy import copy
from getopt import getopt
from contextlib import suppress

YAML_DIRS_TO_COPY={ '../test_data/regtest/schema':'schema',
                    '../test_data/regtest/defaults':'defaults',
                    '../test_data/regtest/config':'config',
                    '../test_data/regtest/runtime':'runtime' } # important: no ending /
YAML_FILES_TO_COPY={ '../test_data/regtest/_expdir_main.yaml': '_main.yaml',
                     '../test_data/regtest/user.yaml': 'user.yaml' }

os.chdir('../../')


