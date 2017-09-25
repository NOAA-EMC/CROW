#! /usr/bin/env python3.6

import os, sys, logging

try:
    import crow.config
except ModuleNotFoundError:
    there=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
    sys.path.append(there)
    import crow.config
from crow.config import Platform
import crow.metascheduler

logging.basicConfig(stream=sys.stderr,level=logging.INFO,
   format='%(module)s:%(lineno)d: %(levelname)8s: %(message)s')
logger=logging.getLogger('setup_expt')

force=False
if len(sys.argv)>1 and sys.argv[1]=='--force':
    force=True
    sys.argv.pop(1)

if len(sys.argv)<2:
    logger.error('Format: setup_expt.py case.yaml')
    exit(1)

yamls=[ 'platform.yaml','template.yaml' ] + \
    sys.argv[1:] + ['runtime.yaml','actions.yaml','workflow.yaml']
conf=crow.config.from_file(*yamls)

logger.info('Remove platforms from configuration.')
for key in list(conf.keys()):
    if isinstance(conf[key],Platform) and key!='platform':
        del conf[key]

EXPDIR=conf.options.EXPDIR
logger.info(f'Run directory: {EXPDIR}')
config_yaml=os.path.join(EXPDIR,'config.yaml')
yaml=crow.config.to_yaml(conf)

try:
    os.makedirs(EXPDIR)
except FileExistsError:
    logger.warning(f'{EXPDIR}: exists')
    if not force:
        logger.error(f'{EXPDIR}: already exists.  Delete or use --force.')
        sys.exit(1)
    logger.warning(f'--force given; will replace config.yaml without '
                   'deleting directory')

logger.info(f'Write the config file: {config_yaml}')
with open(config_yaml,'wt') as fd:
    fd.write(yaml)

suite=conf.workflow

expname=conf.options.experiment_name
logger.info(f'Experiment name: {expname}')

rocoto_xml=crow.metascheduler.to_rocoto(suite)
rocoto_xml_file=os.path.join(EXPDIR,f'{expname}.xml')
logger.info(f'Rocoto XML file: {rocoto_xml_file}')
with open(rocoto_xml_file,'wt') as fd:
    fd.write(rocoto_xml)
logger.info('Workflow XML file is generated.')
logger.info('Use Rocoto to execute this workflow.')

