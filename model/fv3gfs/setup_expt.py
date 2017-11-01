#! /usr/bin/env python3
f'This script requires python 3.6 or later'

import os, sys, logging, glob
from create_comrot import create_COMROT

try:
    import crow.config
except ModuleNotFoundError:
    there=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
    sys.path.append(there)
    import crow.config
from crow.config import Platform
import crow.metascheduler

logging.basicConfig(stream=sys.stderr,level=logging.DEBUG,
   format='%(module)s:%(lineno)d: %(levelname)8s: %(message)s')
logger=logging.getLogger('setup_expt')

force=False
if len(sys.argv)>1 and sys.argv[1]=='--force':
    force=True
    sys.argv.pop(1)

if len(sys.argv)<2:
    logger.error('Format: setup_expt.py case.yaml')
    exit(1)

yamls = [ 'resources.yaml', 'platform.yaml', ]
yamls += sorted(list(glob.glob('validation/*')))
yamls += [ 'places.yaml', 'settings.yaml', 'fv3_enkf_defaults.yaml' ]
yamls += sys.argv[1:] + ['runtime.yaml']
yamls += sorted(list(glob.glob('actions/*')))
yamls += ['workflow.yaml']

conf=crow.config.from_file(*yamls)

logger.info('Remove platforms from configuration.')
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

suite=crow.config.Suite(conf.workflow)
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

