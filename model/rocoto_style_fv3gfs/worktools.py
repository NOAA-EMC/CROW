#! /usr/bin/env python3
f'This python module requires python 3.6 or newer'

import logging, os, io, sys, datetime, glob, shutil, subprocess
from collections import OrderedDict
from copy import copy
logger=logging.getLogger('crow.model.fv3gfs')

try:
    import crow
except ImportError as ie:
    thisdir=os.path.dirname(os.path.abspath(__file__))
    topdir=os.path.realpath(os.path.join(thisdir,"../.."))
    sys.path.append(topdir)
    del thisdir, topdir

level=logging.WARNING
if os.environ.get('WORKTOOLS_VERBOSE','NO') == 'YES':
    level=logging.INFO
logging.basicConfig(stream=sys.stderr,level=level)

import crow.tools
from crow.metascheduler import to_ecflow, to_rocoto
from crow.config import from_dir, Suite, from_file, to_yaml
from crow.tools import Clock

ECFNETS_INCLUDE = "/ecf/ecfnets/include"
SIX_HOURS = datetime.timedelta(seconds=6*3600)

def read_yaml_suite(dir):
    logger.info(f'{dir}: read yaml files specified in _main.yaml')
    conf=from_dir(dir)
    suite=Suite(conf.suite)
    return conf,suite

def make_yaml_files(srcdir,tgtdir):
    if not os.path.exists(tgtdir):
        logger.info(f'{tgtdir}: make directory')
        os.makedirs(tgtdir)
    logger.info(f'{tgtdir}: send yaml files to here')
    logger.info(f'{srcdir}: get yaml files from here')
    for srcfile in glob.glob(f'{srcdir}/*.yaml'):
        srcbase=os.path.basename(srcfile)
        if srcbase.startswith('resources'):   continue
        if srcbase.startswith('settings'):    continue
        tgtfile=os.path.join(tgtdir,srcbase)
        logger.info(f'{srcbase}: copy yaml file')
        shutil.copyfile(srcfile,tgtfile)

    # Deal with the settings:
    doc=from_file(f"{srcdir}/settings.yaml")
    settings_yaml=os.path.join(tgtdir,'settings.yaml')
    logger.info(f'{settings_yaml}: generate file')
    with open(f'{tgtdir}/settings.yaml','wt') as fd:
        fd.write('# This file is automatically generated from:\n')
        fd.write(f'#    {srcdir}/settings.yaml')
        fd.write('# Changes to this file may be overwritten.\n\n')
        fd.write(to_yaml(doc))
        
    # Now the resources:
    resource_basename=doc.settings.resource_file
    resource_srcfile=os.path.join(srcdir,resource_basename)
    resource_tgtfile=os.path.join(tgtdir,'resources.yaml')
    logger.info(f'{resource_srcfile}: use this resource yaml file')
    shutil.copyfile(resource_srcfile,resource_tgtfile)
    logger.info(f'{tgtdir}: yaml files created here')

def loudly_make_dir_if_missing(dirname):
    if dirname and not os.path.exists(dirname):
        logger.info(f'{dirname}: make directory')
        os.makedirs(dirname)

def make_parent_dir(filename):
    loudly_make_dir_if_missing(os.path.dirname(filename))

def make_clocks_for_cycle_range(suite,first_cycle,last_cycle,surrounding_cycles):
    suite_clock=copy(suite.Clock)
    logger.info(f'cycles to write:   {first_cycle:%Ft%T} - {last_cycle:%Ft%T}')
    suite.ecFlow.write_cycles = Clock(
        start=first_cycle,end=last_cycle,step=SIX_HOURS)
    first_analyzed=max(suite_clock.start,first_cycle-surrounding_cycles*SIX_HOURS)
    last_analyzed=min(suite_clock.end,last_cycle+surrounding_cycles*SIX_HOURS)
    logger.info(f'cycles to analyze: {first_analyzed:%Ft%T} - {last_analyzed:%Ft%T}')
    suite.ecFlow.analyze_cycles=Clock(
        start=first_analyzed,end=last_analyzed,step=SIX_HOURS)

def generate_ecflow_suite_in_memory(suite,first_cycle,last_cycle,surrounding_cycles):
    logger.info(f'make suite for cycles: {first_cycle:%Ft%T} - {last_cycle:%Ft%T}')
    make_clocks_for_cycle_range(suite,first_cycle,last_cycle,surrounding_cycles)
    suite_defs, ecf_files = to_ecflow(suite)
    return suite_defs, ecf_files

def write_ecflow_suite_to_disk(targetdir, suite_defs, ecf_files):
    written_suite_defs=OrderedDict()
    logger.info(f'{targetdir}: write suite here')
    for deffile in suite_defs.keys():
        defname = suite_defs[deffile]['name']
        defcontents = suite_defs[deffile]['def']
        #print(f'=== contents of suite def {defname}\n{suite_defs[defname]}')
        filename=os.path.realpath(os.path.join(targetdir,'defs',deffile))
        make_parent_dir(filename)
        logger.info(f'{defname}: {filename}: write suite definition')
        with open(os.path.join(targetdir,filename),'wt') as fd:
            fd.write(defcontents)
        written_suite_defs[defname]=filename
        for setname in ecf_files:
            logger.info(f'{defname}: write ecf file set {setname}')
            for filename in ecf_files[setname]:
                full_fn=os.path.realpath(os.path.join(targetdir,defname,filename)+'.ecf')
                logger.debug(f'{defname}: {setname}: write ecf file {full_fn}')
                make_parent_dir(full_fn)
                with open(full_fn,'wt') as fd:
                    fd.write(ecf_files[setname][filename])
    return written_suite_defs

def get_target_dir_and_check_ecflow_env():
    ECF_HOME=os.environ.get('ECF_HOME',None)

    if not ECF_HOME:
        logger.error('Set $ECF_HOME to location where your ecflow files should reside.')
        return None
    elif not os.environ.get('ECF_PORT',None):
        logger.error('Set $ECF_PORT to the port number of your ecflow server.')
        return None
    elif not os.path.isdir(ECF_HOME):
        logger.error('Directory $ECF_HOME={ECF_HOME} does not exist.  You need to set up your account for ecflow before you can run any ecflow workflows.')
        return None
    
    for file in [ 'head.h', 'tail.h', 'envir-xc40.h' ]:
        yourfile=os.path.join(ECF_HOME,file)
        if not os.path.exists(yourfile):
            logger.warning(f'{yourfile}: does not exist.  I will get one for you.')
            os.symlink(os.path.join(ECFNETS_INCLUDE,file),yourfile)
        else:
            logger.info(f'{yourfile}: exists.')
        
    return ECF_HOME

def create_new_ecflow_workflow(suite,surrounding_cycles=5):
    ECF_HOME=get_target_dir_and_check_ecflow_env()
    if not ECF_HOME: return None,None,None,None
    first_cycle=suite.Clock.start
    last_cycle=min(suite.Clock.end,first_cycle+suite.Clock.step*2)
    suite_defs, ecf_files = generate_ecflow_suite_in_memory(
        suite,first_cycle,last_cycle,surrounding_cycles)
    suite_def_files = write_ecflow_suite_to_disk(
        ECF_HOME,suite_defs,ecf_files)
    return ECF_HOME, suite_def_files, first_cycle, last_cycle

def update_existing_ecflow_workflow(suite,first_cycle,last_cycle,
                                    surrounding_cycles=5):
    ECF_HOME=get_target_dir_and_check_ecflow_env()
    suite_defs, ecf_files = generate_ecflow_suite_in_memory(
        suite,first_cycle,last_cycle,surrounding_cycles)
    suite_def_files = write_ecflow_suite_to_disk(
        ECF_HOME,suite_defs,ecf_files)
    return ECF_HOME, suite_def_files

def load_and_begin_ecflow_suites(ECF_HOME,suite_def_files):
    logger.info(f'{ECF_HOME}: write files for suites: '
                f'{", ".join(suite_def_files.keys())}')
    with crow.tools.chdir(ECF_HOME):
        for suite, file in suite_def_files.items():
            cmd=f'ecflow_client --load {file}'
            logger.info(cmd)
            subprocess.run(cmd,check=False,shell=True)
            cmd=f'ecflow_client --begin {suite}'
            logger.info(cmd)
            subprocess.run(cmd,check=False,shell=True)

def create_and_begin_ecflow_workflow(yamldir,surrounding_cycles=5):
    conf,suite=read_yaml_suite(yamldir)
    loudly_make_dir_if_missing(f'{conf.settings.COM}/log')
    ECF_HOME, suite_def_files, first_cycle, last_cycle = \
        create_new_ecflow_workflow(suite,surrounding_cycles)
    if not ECF_HOME:
        logger.error('Could not create workflow files.  See prior errors for details.')
        return False
    load_and_begin_ecflow_suites(ECF_HOME,suite_def_files)    

# def add_cycles_to_running_ecflow_workflow_at(
#         yamldir,first_cycle,last_cycle,surrounding_cycles=5):
    
