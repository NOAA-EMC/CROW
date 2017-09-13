#! /usr/bin/env python3.6

import os, sys, logging
import crow.config
from crow.config import Platform

logging.basicConfig(stream=sys.stderr,level=logging.INFO,
   format='%(module)s:%(lineno)d: %(levelname)8s: %(message)s')
logger=logging.getLogger('setup_expt')

conf=crow.config.from_file(
    'platform.yaml','options.yaml','runtime.yaml',
    'actions.yaml','workflow.yaml' )

force = len(sys.argv)>1 and sys.argv[1] == '--force'

# Store evaluated versions of options and platform instead of storing
# the original !expand, !calc, !FirstTrue, etc.  Skip all platforms
# except the one enabled.
logger.info('Evaluate options and platform.')
crow.config.evaluate_immediates(conf,recurse=False)
for key,val in conf.items():
    if isinstance(val,Platform) and key!='platform': continue
    crow.config.evaluate_immediates(val,recurse=True)

run_dir=conf.options.run_dir
logger.info(f'Run directory: {run_dir}')
config_yaml=os.path.join(run_dir,'config.yaml')
logger.info(f'Config file: {config_yaml}')
yaml=crow.config.to_yaml(conf)

try:
    os.makedirs(run_dir)
except FileExistsError:
    logger.warning(f'{run_dir}: exists')
    if not force:
        logger.error(f'{run_dir}: already exists.  Delete or use --force.')
        sys.exit(1)
    logger.warning(f'--force given; will replace config.yaml without '
                   'deleting directory')

with open(config_yaml,'wt') as fd:
    fd.write(yaml)

logger.info(f'Experiment is set up.  Run setup_workflow.py {run_dir}')
