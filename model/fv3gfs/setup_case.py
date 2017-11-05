#! /usr/bin/env python3
f'This script requires python 3.6 or later'

import os, sys, logging, glob, io, getopt, re
from collections.abc import Sequence

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__),'../..')))

from create_comrot import create_COMROT
import crow.config, crow.metascheduler
from crow.config import Platform

logger=logging.getLogger("setup_case")

def epicfail(why):
    logger.error(why)
    sys.exit(1)

def follow_main(fd,reldir,more_globals):
    logger.debug(f"{reldir}: enter directory")
    mainfile=os.path.join(reldir,"_main.yaml")

    includes=[ "*.yaml" ]
    if os.path.exists(mainfile):
        logger.debug(f"{mainfile}: read \"include\" array")
        maindat=crow.config.from_file(mainfile)
        maindat.update(more_globals)
        if "include" not in maindat or \
           not isinstance(maindat.include,Sequence):
            epicfail(f"{mainfile} has no \"include\" array")
        includes=maindat.include

    logger.debug(f"{reldir}: scan {includes}")

    literals=set()
    # First pass: scan for literal files:
    for item in includes:
        if not re.search(r'[*?\[\]{}]',item):
            literals.add(item)

    # Second pass: read files:
    included=set()
    for item in includes:
        if item in included: continue
        is_literal=item in literals
        if is_literal:
            paths=[ os.path.join(reldir,item) ]
        else:
            paths=[ x for x in glob.glob(os.path.join(reldir,item)) ]
        logger.debug(f"{reldir}: {item}: paths = {paths}")
        for path in paths:
            basename=os.path.basename(path)
            if basename in included: continue
            if not is_literal and basename in literals: continue
            if basename == "_main.yaml": continue
            if os.path.isdir(path):
                follow_main(fd,path,more_globals)
            else:
                logger.debug(f"{path}: read yaml")
                included.add(basename)
                with open(path,"rt") as pfd:
                    fd.write(f"#--- {path}\n")
                    fd.write(pfd.read())
                    fd.write(f"\n#--- end {path}\n")

def read_contents(case):
    for case_file in [ case,f"{case}.yaml",f"cases/{case}",
                       f"cases/{case}.yaml","/" ]:
        if os.path.exists(case_file) and case_file!='/':
            logger.info(f"{case_file}: file for this case")
            break
    if case_file == "/":
        epicfail(f"{case}: no such case; pick one from in cases/")
    if not os.path.exists("user.yaml"):
        epicfail("Please copy user.yaml.default to user.yaml and fill in values.")
    with io.StringIO() as yfd:
        follow_main(yfd,".",{ "case_yaml":case_file, "user_yaml":"user.yaml" })
        yaml=yfd.getvalue()
    return crow.config.from_string(yaml)
    
def main():
    ( optval, args ) = getopt.getopt(sys.argv[1:],"v",["verbose","force"])
    options=dict(optval)
    level=logging.INFO
    if '-v' in options or '--verbose' in options:
        level=logging.DEBUG
    logging.basicConfig(stream=sys.stderr,level=level)
    force="--force" in options

    if len(args)!=1:
        sys.stderr.write("Format: setup_case.py [-v] [--force] case-name\n")
        exit(1)

    case=args[0]

    logger.info(f"read case {case}")
    conf=read_contents(case)
    logger.info("Remove platforms from configuration.")
    for key in list(conf.keys()):
        if isinstance(conf[key],Platform) and key!='platform':
            del conf[key]
    
    EXPDIR=conf.places.EXPDIR
    logger.info(f'Run directory: {EXPDIR}')
    config_yaml=os.path.join(EXPDIR,'config.yaml')
            
    try:
        os.makedirs(EXPDIR)
    except FileExistsError:
        logger.warning(f'{EXPDIR}: exists')
        if not force:
            logger.error(f'{EXPDIR}: already exists.  Delete or use --force.')
            sys.exit(1)
        logger.warning(f'--force given; will replace config.yaml without '
                       'deleting directory')
    
    create_COMROT(conf)
    
    chosen_workflow=conf.case.workflow
    conf.workflow=conf[chosen_workflow]

    suite=crow.config.Suite(conf[chosen_workflow])
    doc=crow.config.document_root(suite)
    
    expname=conf.case.experiment_name
    logger.info(f'Experiment name: {expname}')
    
    logger.info(f'Generate suite definition')
    rocoto_xml=crow.metascheduler.to_rocoto(suite)
    logger.info(f'Prepare cached YAML')
    yaml=crow.config.to_yaml(doc)
    
    logger.info(f'Write the config file: {config_yaml}')
    with open(config_yaml,'wt') as fd:
        fd.write(yaml)
    
    rocoto_xml_file=os.path.join(EXPDIR,f'{expname}.xml')
    logger.info(f'Rocoto XML file: {rocoto_xml_file}')
    with open(rocoto_xml_file,'wt') as fd:
        fd.write(rocoto_xml)
    logger.info('Workflow XML file is generated.')
    logger.info('Use Rocoto to execute this workflow.')

if __name__ == "__main__":
    main()
