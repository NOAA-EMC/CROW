#!/usr/bin/env python3

import logging, os, io, sys, datetime, glob, shutil, subprocess, re, itertools, collections
from collections import OrderedDict
from copy import copy
from getopt import getopt
from contextlib import suppress

sys.path.append(os.getcwd() + "/../../")

import crow
import crow.tools, crow.config
from crow.metascheduler import to_ecflow, to_rocoto, to_dummy
from crow.config import from_dir, Suite, from_file, to_yaml
from crow.tools import Clock
import worktools as wt

YAML_DIRS_TO_COPY={ '../test_data/regtest/schema':'schema',
                    '../test_data/regtest/defaults':'defaults',
                    '../test_data/regtest/config':'config',
                    '../test_data/regtest/runtime':'runtime' } # important: no ending /
YAML_FILES_TO_COPY={ '../test_data/regtest/_expdir_main.yaml': '_main.yaml',
                     '../test_data/regtest/user.yaml': 'user.yaml' }


def reg_case_setup():
    
    crow.set_superdebug(True)           # superdebug on
    force=True                          # Force rewrite
    skip_comrot=False                    # Not skip comrot
    force_platform_rewrite=True         # Overwrite platform every time

    case_name='regression_case'
    experiment_name='regtest_tmp'

    valid_platforms=wt.sandbox_platforms("../test_data/regtest/platforms/")
    platdoc = wt.select_platform(None,valid_platforms)

    EXPDIR = wt.make_yaml_files_in_expdir(
        os.path.abspath('../'),case_name,experiment_name,platdoc,force,
        skip_comrot,force_platform_rewrite)

    doc=wt.from_dir(EXPDIR,validation_stage='setup')
    suite=Suite(doc.suite)
    wt.to_dummy(suite)
    suite_doc=suite._globals()['doc']
    wt.make_config_files_in_expdir(suite_doc,EXPDIR)

    wt.create_COMROT(doc,force)

    print()
    print(f'CROW Regression Case set up completed')
    print()
    print(f'  YAML files:     {EXPDIR}')
    print(f'  Config files:   {EXPDIR}')
    print(f'  COM directory:  {doc.places.ROTDIR}')
    print()
    print('Now you should make a workflow:')
    print()
    print(f'  Rocoto: ./make_rocoto_xml_for.sh {EXPDIR}')
    print(f'  ecFlow: ./make_ecflow_files_for.sh -v {EXPDIR} SDATE EDATE')
    print()


def reg_ecflow():
    return(0)

def reg_rocoto():
    return(0)

def reg_compare():
    return(0)

if __name__ == '__main__':
    print(f'CROW Regression Case begins')
    reg_case_setup()
    reg_ecflow()
    reg_rocoto()
    reg_compare()
    print(os.getcwd())