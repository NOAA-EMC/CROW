#! /usr/bin/env python3

import unittest, os, sys, logging

from context import crow

from crow import config
from crow import metascheduler
from crow.sysenv import JobResourceSpec
from crow.sysenv import get_parallelism
from crow.sysenv import get_scheduler

logging.basicConfig(stream=sys.stderr,level=logging.INFO)
logger = logging.getLogger()

class TestAprunCrayMPI(unittest.TestCase):
    @classmethod
    def setUpClass(self):

        settings={ 'mpi_runner':'mpiexec',
           'physical_cores_per_node':24,
           'logical_cpus_per_core':2,
           'hyperthreading_allowed':True }
        
        self.par=get_parallelism('AprunCrayMPI',settings)
        self.sch=get_scheduler('LSFAlps',settings)

    def test_AprunCrayMPI_big(self):
        
        ranks=[ { 'mpi_ranks':12, 'hyperthreads':1, 'OMP_NUM_THREADS':4, 'exe':'exe1',
                  'AprunCrayMPI_extra':[ '-gdb', '-envall' ] },
                { 'mpi_ranks':48,                   'OMP_NUM_THREADS':1, 'exe':'exe2',
                  'AprunCrayMPI_extra':'-envall' },
                { 'mpi_ranks':200,'hyperthreads':1,                      'exe':'exe2' }  ]

        jr=JobResourceSpec(ranks)
        cmd=self.par.make_ShellCommand(jr)
        res=self.sch.rocoto_resources(jr)

        if os.environ.get('LOG_LEVEL','None') != "INFO":
            logging.disable(os.environ.get('LOG_LEVEL',logging.CRITICAL))
        logger.info('\n\nnmax_notMPI ranks:\n'+str(ranks) )
        logger.info(    'nmax_notMPI cmd  :\n'+str(cmd) )
        logger.info(    'nmax_notMPI res  :\n'+str(res) )
        logging.disable(logging.NOTSET)  

        logging.info("assertions not set yet")
        self.assertTrue( 'True' == 'True' )
         
    def test_AprunCrayMPI_max_ppn(self):
        
        ranks=[ { 'mpi_ranks':12, 'max_ppn':2, 'exe':'doit' },
                { 'mpi_ranks':12, 'max_ppn':4, 'exe':'doit' } ]

        jr=JobResourceSpec(ranks)
        cmd=self.par.make_ShellCommand(jr)
        res=self.sch.rocoto_resources(jr)

        if os.environ.get('LOG_LEVEL','None') != "INFO":
            logging.disable(os.environ.get('LOG_LEVEL',logging.CRITICAL))
        logger.info('\n\nnmax_notMPI ranks:\n'+str(ranks) )
        logger.info(    'nmax_notMPI cmd  :\n'+str(cmd) )
        logger.info(    'nmax_notMPI res  :\n'+str(res) )
        logging.disable(logging.NOTSET)  

        logging.info("assertions not set yet")
        self.assertTrue( 'True' == 'True' )
