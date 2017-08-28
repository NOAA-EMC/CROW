import itertools
from io import StringIO

from crow.sysenv.exceptions import *
from crow.sysenv.util import ranks_to_nodes_ppn
from crow.sysenv.spec import JobResourceSpec, node_ppn_pairs_for_mpi_spec

from crow.sysenv.schedulers.base import Scheduler as BaseScheduler

from collections import Sequence

__all__=['Scheduler']

class Scheduler(BaseScheduler):

    def __init__(self,settings):
        self.settings=dict(settings)
        self.cores_per_node=int(settings['physical_cores_per_node'])
        self.cpus_per_core=int(settings.get('logical_cpus_per_core',1))
        self.hyperthreading_allowed=bool(
            settings.get('hyperthreading_allowed',False))
        self.rocoto_name='MoabTorque'
        self.indent_text=str(settings.get('indent_text','  '))

    ####################################################################

    # Public methods

    def rocoto_accounting(self,spec,indent=0):
        space=self.indent_text
        sio=StringIO()
        if 'queue' in spec:
            sio.write(f'{indent*space}<queue>{spec.queue!s}</queue>\n')
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

        # MPI program.  Split into (nodes,ranks_per_node) pairs.
        nodes_ranks=node_ppn_pairs_for_mpi_spec(
            spec,self.max_ranks_per_node,self.can_merge_ranks)

        return indent*space+'<nodes>' \
            + '+'.join([f'{n}:ppn={p}' for n,p in nodes_ranks ]) \
            + '</nodes>\n'

    def max_ranks_per_node(rank_spec):
        can_hyper=self.hyperthreading_allowed
        max_per_node=self.cores_per_node
        if can_hyper and rank_spec.get('hyperthreading',False):
            max_per_node*=self.cpus_per_core
        threads_per_node=max_per_node
        max_per_node //= max(1,rank_spec.get('OMP_NUM_THREADS',1))
        if max_per_node<1:
            raise MachineTooSmallError(f'Specification too large for node: max {threads_per_node} for {rank_spec!r}')
        return max_per_node

    def can_merge_ranks(rank_set_1,rank_set_2):
        R1, R2 = rank_set_1, rank_set_2
        if R1['separate_node'] or R2['separate_node']: return False

        can = R1['OMP_NUM_THREADS']==R2['OMP_NUM_THREADS'] and \
              R1.get('max_ppn',0)==R2.get('max_ppn',0)
        if self.hyperthreading_allowed:
            same = same and R1.get('hyperthreads',1) == \
                            R2.get('hyperthreads',1)
        return same

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

