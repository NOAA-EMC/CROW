#!/usr/bin/env python3

import logging, os, io, sys, datetime, glob, shutil, subprocess, re, itertools, collections
from collections import OrderedDict
from copy import copy
from getopt import getopt
from contextlib import suppress
logger=logging.getLogger('crow.model.fv3gfs')

sys.path.append(os.getcwd() + "/../../")

import crow
import crow.tools, crow.config
from crow.metascheduler import to_ecflow, to_rocoto, to_dummy
from crow.config import from_dir, Suite, from_file, to_yaml
from crow.tools import Clock    #import worktools as wt

from worktools import loudly_make_dir_if_missing
from worktools import loudly_make_symlink
from worktools import make_parent_dir, find_available_platforms, sandbox_platforms
from worktools import select_platform, create_COMROT, find_case_yaml_file_for
from worktools import read_yaml_suite, make_config_files_in_expdir
from worktools import make_yaml_files_in_expdir, make_clocks_for_cycle_range
from worktools import generate_ecflow_suite_in_memory, make_ecflow_job_and_out_directories
from worktools import make_log_directories, write_ecflow_suite_to_disk
from worktools import get_target_dir_and_check_ecflow_env, check_or_populate_ecf_include
from worktools import create_new_ecflow_workflow, update_existing_ecflow_workflow
from worktools import load_ecflow_suites, begin_ecflow_suites, make_rocoto_xml

def reg_case_setup():
    
    YAML_DIRS_TO_COPY={ '../test_data/regtest/schema':'schema',
                    '../test_data/regtest/defaults':'defaults',
                    '../test_data/regtest/config':'config',
                    '../test_data/regtest/runtime':'runtime' } # important: no ending /
    YAML_FILES_TO_COPY={ '../test_data/regtest/_expdir_main.yaml': '_main.yaml',
                     '../test_data/regtest/user.yaml': 'user.yaml' }

    logger.setLevel(logging.INFO)
    crow.set_superdebug(True)           # superdebug on
    force=True                          # Force rewrite
    skip_comrot=False                   # Not skip comrot
    force_platform_rewrite=True         # Overwrite platform every time

    case_name='regression_case'
    experiment_name='regtest_tmp'
      
    userfile = list(YAML_FILES_TO_COPY.keys())[list(YAML_FILES_TO_COPY.values()).index('user.yaml')]
    
    valid_platforms=sandbox_platforms(userfile,"../test_data/regtest/platforms/")
    platdoc = select_platform(None,valid_platforms)

    EXPDIR = make_yaml_files_in_expdir(
        os.path.abspath('../test_data/regtest/'),YAML_DIRS_TO_COPY,YAML_FILES_TO_COPY,case_name,experiment_name,platdoc,force,
        skip_comrot,force_platform_rewrite)

    doc=from_dir(EXPDIR,validation_stage='setup')
    suite=Suite(doc.suite)
    to_dummy(suite)
    suite_doc=suite._globals()['doc']
    make_config_files_in_expdir(suite_doc,EXPDIR)

    create_COMROT(doc,force)

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