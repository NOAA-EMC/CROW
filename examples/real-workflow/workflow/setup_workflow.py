#! /usr/bin/env python3.6

import sys, os, logging
import crow.config
import crow.metascheduler

logging.basicConfig(stream=sys.stderr,level=logging.INFO,
   format='%(module)s:%(lineno)d: %(levelname)8s: %(message)s')
logger=logging.getLogger('setup_workflow')

run_dir=sys.argv[1]
logger.info(f'Run directory: {run_dir}')
config_yaml=os.path.join(run_dir,'config.yaml')
logger.info(f'Config file: {config_yaml}')
conf=crow.config.from_file(config_yaml)
suite=conf.workflow

expname=conf.options.experiment_name
logger.info(f'Experiment name: {expname}')

rocoto_xml=crow.metascheduler.to_rocoto(suite)
rocoto_xml_file=os.path.join(run_dir,f'{expname}.xml')
logger.info(f'Rocoto XML file: {rocoto_xml_file}')
with open(rocoto_xml_file,'wt') as fd:
    fd.write(rocoto_xml)
logger.info('Workflow XML file is generated.')
logger.info('Use Rocoto to execute this workflow.')
