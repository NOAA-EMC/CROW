import itertools
from io import StringIO

from crow.sysenv.exceptions import *
from crow.sysenv.util import ranks_to_nodes_ppn
from crow.sysenv.jobs import JobResourceSpec
from crow.sysenv.nodes import GenericNodeSpec

from crow.sysenv.schedulers.base import Scheduler as BaseScheduler

from collections import Sequence

__all__=['Scheduler']

class Scheduler(BaseScheduler):

    def __init__(self,settings):
        self.settings=dict(settings)
        self.nodes=GenericNodeSpec(settings)
        self.rocoto_name='MoabTorque'
        self.indent_text=str(settings.get('indent_text','  '))

    ####################################################################

    # Public methods

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

