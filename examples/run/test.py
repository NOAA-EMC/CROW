#! /usr/bin/env python3.6

import sys, os, logging, subprocess

import crow
import crow.config
import crow.metascheduler
import crow.sysenv

logging.basicConfig(stream=sys.stderr,level=logging.INFO)

settings={ 'mpi_runner':'mpiexec',
           'physical_cores_per_node':24,
           'logical_cpus_per_core':2,
           'hyperthreading_allowed':True }

par=crow.sysenv.get_parallelism('HydraIMPI',settings)

ranks=[ 
    { 'mpi_ranks':12, 'hyperthreads':1, 'OMP_NUM_THREADS':4, 'exe':'exe1',
      'HydraIMPI_extra':[ '-gdb', '-envall' ] },
    { 'mpi_ranks':48,                   'OMP_NUM_THREADS':1, 'exe':'exe2',
      'HydraIMPI_extra':'-envall' },
    { 'mpi_ranks':200,'hyperthreads':1,                      'exe':'exe2' }
    ]

jr=crow.sysenv.JobResourceSpec(ranks)

cmd=par.make_ShellCommand(jr)

print(str(cmd))

if os.path.exists('file1'): os.unlink('file1')
if os.path.exists('file2'): os.unlink('file2')

cmd=crow.sysenv.ShellCommand(['/bin/sh','-c', 'cat $FILE1 $FILE2'],
      files=[ { 'name':'file1', 'content':'hello ' }, 
              { 'name':'file2', 'content':'world\n' } ],
      env={ 'FILE1':'file1', 'FILE2':'file2' },
      cwd='.' )
result=cmd.run(stdout=subprocess.PIPE,encoding='ascii')
print(repr(result.stdout))
assert(result.stdout=='hello world\n')

if os.path.exists('file1'): os.unlink('file1')
if os.path.exists('file2'): os.unlink('file2')

#config=crow.config.from_file(
#    'platform.yml','templates.yml','actions.yml','workflow.yml')

#print(crow.met.Sascheduler.to_rocoto(config.my_fancy_workflow))
