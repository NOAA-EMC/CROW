import itertools
from crow.sysenv.exceptions import *
from crow.sysenv.util import ranks_to_nodes_ppn
from crow.sysenv.spec import JobResourceSpec
from collections import Sequence

__all__=['Scheduler']

class Scheduler(object):

    def __init__(self,settings):
        self.settings=dict(settings)
        self.cores_per_node=int(settings['physical_cores_per_node'])
        self.cpus_per_core=int(settings.get('logical_cpus_per_core',1))
        self.hyperthreading_allowed=bool(
            settings.get('hyperthreading_allowed',False))
        self.rocoto_name='MoabTorque'

    def rocoto_accounting(self,spec,indent=''):
        return ''

    def rocoto_resources(self,spec,indent=''):
        if not isinstance(spec,JobResourceSpec):
            spec=JobResourceSpec(spec)

        if spec.is_pure_serial():
            if spec[0].is_exclusive() in [True,None]:
                return indent+'<nodes>1:ppn=2</nodes>\n'
            else:
                return indent+'<cores>1</cores>\n'
        elif spec.is_pure_openmp():
            # Pure threaded.  Treat as exclusive serial.
            return indent+'<nodes>1:ppn=2</nodes>\n'

        # MPI program.  Split into (nodes,ranks_per_node) pairs.
        nodes_ranks=self.node_ppn_pairs_for_mpi_spec(spec)

        return '<nodes>' \
            + '+'.join([f'{n}:ppn={p}' for n,p in nodes_ranks ]) \
            + '</nodes>\n'

    def node_ppn_pairs_for_mpi_spec(self,spec):
        """!Given a JobResourceSpec that represents an MPI program, express 
        it in (nodes,ranks_per_node) pairs."""

        def remove_exe(rank):
            if 'exe' in rank: del rank['exe']

        # Merge ranks with same specifications:
        collapsed=spec.simplify(self.merge_similar_ranks,remove_exe)

        # Get the (nodes,ppn) pairs for all ranks:
        nodes_ranks=list()
        can_hyper=self.hyperthreading_allowed
        for block in collapsed:
            max_per_node=self.cores_per_node
            if can_hyper and block.get('hyperthreading',False):
                max_per_node*=self.cpus_per_core
            threads_per_node=max_per_node
            max_per_node //= max(1,block.get('OMP_NUM_THREADS',1))
            if max_per_node<1:
                raise MachineTooSmallError(f'Specification too large for node: max {threads_per_node} for {block!r}')
            ranks=block['mpi_ranks']
            kj=ranks_to_nodes_ppn(max_per_node,ranks)
            nodes_ranks.extend(kj)
        assert(nodes_ranks)
        return nodes_ranks

    def merge_similar_ranks(self,ranks):
        if not isinstance(ranks,Sequence):
            raise TypeError('ranks argument must be a Sequence not a %s'%(
                type(ranks).__name__,))
        is_threaded=any([bool(rank.is_openmp()) for rank in ranks])
        i=0
        while i<len(ranks)-1:
            if ranks[i]['separate_node']:
                i=i+1
                continue

            same = ranks[i]['OMP_NUM_THREADS']==ranks[i+1]['OMP_NUM_THREADS'] and \
                   ranks[i].get('max_ppn',0)==ranks[i+1].get('max_ppn',0)

            if self.hyperthreading_allowed:
                same = same and ranks[i].get('hyperthreads',1) == \
                              ranks[i+1].get('hyperthreads',1)

            if same:
                ranks[i]=ranks[i].new_with(
                    mpi_ranks=ranks[i]['mpi_ranks']+ranks[i+1]['mpi_ranks'])
                del ranks[i+1]
            else:
                i=i+1

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

