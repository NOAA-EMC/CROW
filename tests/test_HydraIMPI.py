#! /usr/bin/env python3
f'This script requires python 3.6 or later'

import unittest
from context import crow

import sys, os, logging, subprocess

from crow import config
from crow import metascheduler
from crow.sysenv import JobResourceSpec
from crow.sysenv import get_parallelism
from crow.sysenv import get_scheduler


class TestHydraIMPI(unittest.TestCase):
    @classmethod
    def setUpClass(hydra):

        settings={ 'mpi_runner':'mpiexec',
           'physical_cores_per_node':24,
           'logical_cpus_per_core':2,
           'hyperthreading_allowed':True }
        
        ranks=[ 
            { 'mpi_ranks':12, 'hyperthreads':1, 'OMP_NUM_THREADS':4, 'exe':'exe1',
              'HydraIMPI_extra':[ '-gdb', '-envall' ] },
            { 'mpi_ranks':48,                   'OMP_NUM_THREADS':1, 'exe':'exe2',
               'HydraIMPI_extra':'-envall' },
            { 'mpi_ranks':200,'hyperthreads':1,                      'exe':'exe2' }
            ]
        
        hydra.par=get_parallelism('HydraIMPI',settings)
        hydra.sch=get_scheduler('MoabTorque',settings)
        hydra.jr=JobResourceSpec(ranks)

    def test_HydraIMPI_shellCommand(hydra):
        cmd=hydra.par.make_ShellCommand(hydra.jr)
        hydra.assertTrue(str(cmd)=="ShellCommand(command=['mpiexec', '-gdb', '-envall', '-np', '12', '/usr/bin/env', 'OMP_NUM_THREADS=4', 'exe1', ':', '-envall', '-np', '48', '/usr/bin/env', 'OMP_NUM_THREADS=1', 'exe2', ':', '-np', '200', 'exe2'], env=None, cwd=None, files=[ ])")
         
    def test_HydraIMPI_resource(hydra):   
        res=hydra.sch.rocoto_resources(hydra.jr)
        hydra.assertTrue(str(res)=='<nodes>2:ppn=6+2:ppn=24+2:ppn=23+7:ppn=22</nodes>\n')
