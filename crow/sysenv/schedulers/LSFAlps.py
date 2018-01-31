import itertools, math
from io import StringIO

import crow.tools as tools
from crow.sysenv.exceptions import *
from crow.sysenv.util import ranks_to_nodes_ppn
from crow.sysenv.jobs import JobResourceSpec
from crow.sysenv.nodes import GenericNodeSpec

from crow.sysenv.schedulers.base import Scheduler as BaseScheduler

from collections import Sequence

__all__=['Scheduler']

class Scheduler(BaseScheduler):

    def __init__(self,settings,**kwargs):
        self.settings=dict(settings)
        self.settings.update(kwargs)
        self.nodes=GenericNodeSpec(settings)
        self.rocoto_name='lsf'
        self.indent_text=str(settings.get('indent_text','  '))

    ####################################################################

    # Generation of batch cards

    def batch_accounting(self,spec,**kwargs):
        if kwargs:
            spec=dict(spec,**kwargs)
        space=self.indent_text
        sio=StringIO()
        if 'queue' in spec:
            sio.write(f'#BSUB -q {spec["queue"]!s}\n')
        if 'project' in spec:
            sio.write(f'#BSUB -P {spec["project"]!s}\n')
        if 'account' in spec:
            sio.write(f'#BSUB -P {spec["account"]!s}\n')
        if 'jobname' in spec:
            sio.write(f'#BSUB -J {spec["jobname"]!s}\n')
        ret=sio.getvalue()
        sio.close()
        return ret

    def batch_resources(self,spec,**kwargs):
        if kwargs:
            spec=dict(spec,**kwargs)
        space=self.indent_text
        sio=StringIO()
        if not isinstance(spec,JobResourceSpec):
            spec=JobResourceSpec(spec)
            
        result=''
        if spec[0].get('walltime',''):
            dt=tools.to_timedelta(spec[0]['walltime'])
            dt=dt.total_seconds()
            hours=int(dt//3600)
            minutes=int((dt%3600)//60)
            seconds=int(math.floor(dt%60))
            sio.write(f'#BSUB -W {hours}:{minutes:02d}\n')
       
        if spec[0].get('memory',''):
            memory=spec[0]['memory']
            bytes=tools.memory_in_bytes(memory)
            megabytes=int(math.ceil(bytes/1048576.))
            sio.write(f'#BSUB -R rusage[mem={megabytes:d}]\n')
        else:
            sio.write(f'#BSUB -R rusage[mem=2000]\n')

        if spec[0].get('outerr',''):
            sio.write(f'#BSUB -o {spec[0]["outerr"]}\n')
        else:
            if spec[0].get('stdout',''):
                sio.write('#BSUB -o {spec[0]["stdout"]}\n')
            if spec[0].get('stderr',''):
                sio.write('#BSUB -e {spec[0]["stderr"]}\n')
        # --------------------------------------------------------------

        # With LSF+ALPS on WCOSS Cray, to my knowledge, you can only
        # request one node size for all ranks.  This code calculates
        # the largest node size required (hyperthreading vs. non)

        requested_nodes=1

        nodesize=max([ self.nodes.node_size(r) for r in spec ])

        if not spec.is_pure_serial() and not spec.is_pure_openmp():
            # This is an MPI program.
            nodes_ranks=self.nodes.to_nodes_ppn(spec)
            requested_nodes=sum([ n for n,p in nodes_ranks ])
        sio.write('#BSUB -extsched CRAYLINUX[]\n')
        if self.settings.get('use_export_nodes',True):
            sio.write(f'export NODES={requested_nodes}')
        else:
            sio.write("#BSUB -R '1*{select[craylinux && !vnode]} + ")
            sio.write('%d'%requested_nodes)
            sio.write("*{select[craylinux && vnode]span[")
            sio.write(f"ptile={nodesize}] cu[type=cabinet]}}'")
        
        ret=sio.getvalue()
        sio.close()
        return ret

    ####################################################################

    # Generation of Rocoto XML

    def rocoto_accounting(self,spec,indent=0):
        space=self.indent_text
        sio=StringIO()
        if 'queue' in spec:
            sio.write(f'{indent*space}<queue>{spec.queue!s}</queue>\n')
        if 'account' in spec:
            sio.write(f'{indent*space}<account>{spec.account!s}</account>\n')
        if 'project' in spec:
            sio.write(f'{indent*space}<account>{spec.project!s}</account>\n')
        if 'partition' in spec:
            sio.write(f'{indent*space}<native>-l partition='
                      f'{spec.partition!s}</native>\n')
        if 'account' in spec:
            sio.write(f'{indent*space}<account>{spec.account!s}</account>\n')
        ret=sio.getvalue()
        sio.close()
        return ret

    def rocoto_resources(self,spec,indent=0):
        space=self.indent_text
        if not isinstance(spec,JobResourceSpec):
            spec=JobResourceSpec(spec)

        if spec.is_pure_serial():
            if spec[0].is_exclusive() in [True,None]:
                return indent*space+'<nodes>1:ppn=2</nodes>\n'
            else:
                return indent*space+'<cores>1</cores>\n'
        elif spec.is_pure_openmp():
            # Pure threaded.  Treat as exclusive serial.
            return indent*space+'<nodes>1:ppn=2</nodes>\n'

        # This is an MPI program.

        # Split into (nodes,ranks_per_node) pairs.  Ignore differeing
        # executables between ranks while merging them (del_exe):
        nodes_ranks=self.nodes.to_nodes_ppn(
            spec,can_merge_ranks=self.nodes.same_except_exe)

        return indent*space+'<nodes>' \
            + '+'.join([f'{n}:ppn={p}' for n,p in nodes_ranks ]) \
            + '</nodes>\n'

def test():
    settings={ 'physical_cores_per_node':24,
               'logical_cpus_per_core':2,
               'hyperthreading_allowed':True }
    sched=Scheduler(settings)

    # MPI + OpenMP program test
    input1=[
        {'mpi_ranks':5, 'OMP_NUM_THREADS':12},
        {'mpi_ranks':7, 'OMP_NUM_THREADS':12},
        {'mpi_ranks':7} ]
    spec1=JobResourceSpec(input1)
    result=sched.rocoto_resources(spec1)
    assert(result=='<nodes>6:ppn=2+1:ppn=7</nodes>\n')

    # Serial program test
    input2=[ { 'exe':'echo', 'args':['hello','world'], 'exclusive':False } ]
    spec2=JobResourceSpec(input2)
    assert(sched.rocoto_resources(spec2)=='<cores>1</cores>\n')

    # Exclusive serial program test
    input3=[ { 'exe':'echo', 'args':['hello','world 2'], 'exclusive':True } ]
    spec3=JobResourceSpec(input3)
    result=sched.rocoto_resources(spec3)
    assert(result=='<nodes>1:ppn=2</nodes>\n')

    # Pure openmp test
    input4=[ { 'OMP_NUM_THREADS':20 } ]
    spec4=JobResourceSpec(input4)
    result=sched.rocoto_resources(spec4)
    assert(result=='<nodes>1:ppn=2</nodes>\n')

    # Too big for node
    try:
        input5=[ { 'OMP_NUM_THREADS':200, 'mpi_ranks':3 } ]
        spec5=JobResourceSpec(input5)
        result=sched.rocoto_resources(spec5)
        assert(False)
    except MachineTooSmallError:
        pass # success!

