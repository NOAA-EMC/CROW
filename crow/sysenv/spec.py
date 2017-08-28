from collections import UserList, Mapping, Sequence

__all__=['JobRankSpec','JobResourceSpec']

JOB_RANK_SPEC_TEMPLATE={
    'mpi_ranks':0,
    'OMP_NUM_THREADS':0,
    'hyperthreading':False }

MISSING=object() # special constant for missing arguments

class JobRankSpec(Mapping):
    def __init__(self,*,OMP_NUM_THREADS=0,mpi_ranks=0,
                 exe=MISSING,args=MISSING,exclusive=True,
                 separate_node=False):
        self.__spec={
            'mpi_ranks':max(0,int(mpi_ranks)),
            'exclusive':bool(exclusive),
            'separate_node':separate_node,
            'OMP_NUM_THREADS':max(0,int(OMP_NUM_THREADS)),
            'exe':( None if exe is MISSING else exe ),
            'args':( [] if args is MISSING else list(args) ) }
        if not isinstance(exe,str) and exe is not MISSING and \
           exe is not None:
            raise TypeError('exe must be a string, not a %s'%(
                type(exe).__name__,))

    def is_exclusive(self):
        """!Trinary accessor - True, False, None (unset).  None indicates 
        no request was made for or against exclusive."""
        return self.__spec['exclusive']

    def is_pure_serial(self):
        return not self.is_mpi() and not self.is_openmp()
    def is_openmp(self):
        return self['OMP_NUM_THREADS']>0
    def is_mpi(self):
        return self['mpi_ranks']>0

    def simplify(self,adapt):
        js=JobRankSpec(**self.__spec)
        adapt(js.__spec)
        return js

    def new_with(self,*args,**kwargs):
        """!Creates a new JobRankSpec with the given modifications.  The
        calling convention is the same as dict.update()."""
        newspec=dict(self.__spec)
        newspec.update(*args,**kwargs)
        return JobRankSpec(**newspec)

    # Implement Mapping abstract methods:
    def __getitem__(self,key): return self.__spec[key]
    def __len__(self): return len(self.__spec)
    def __iter__(self):
        for k in self.__spec:
            yield k

    def __repr__(self):
        typ=type(self).__name__
        return typ+'{'+\
            ','.join([f'{repr(k)}:{repr(v)}' for k,v in self.items()]) + \
            '}'

class JobResourceSpec(Sequence):
    def __init__(self,specs):
        self.__specs=[ JobRankSpec(**spec) for spec in specs ]

    # Implement Sequence abstract methods:
    def __getitem__(self,index): return self.__specs[index]
    def __len__(self):           return len(self.__specs)

    def simplify(self,adapt_resource_spec,adapt_rank_spec):
        new=JobResourceSpec(
            [ spec.simplify(adapt_rank_spec) for spec in self ])
        adapt_resource_spec(new.__specs)
        return new

    def has_threads(self):
        return any([ spec.is_openmp() for spec in self])

    def total_ranks(self):
        return sum([ spec['mpi_ranks'] for spec in self])

    def is_pure_serial(self):
        return len(self)<2 and self[0].is_pure_serial()

    def is_pure_openmp(self):
        return len(self)<2 and not self[0].is_mpi() and self[0].is_openmp()

    def __repr__(self):
        typ=type(self).__name__
        return f'{typ}[{", ".join([repr(r) for r in self])}]'

########################################################################
 
def node_ppn_pairs_for_mpi_spec(self,spec,max_per_node_function,
                                rank_comparison_function):
    """!Given a JobResourceSpec that represents an MPI program, express 
    it in (nodes,ranks_per_node) pairs."""
    def remove_exe(rank):
        if 'exe' in rank: del rank['exe']
     # Merge ranks with same specifications:
    collapsed=spec.simplify(self._merge_similar_ranks,remove_exe)
     # Get the (nodes,ppn) pairs for all ranks:
    nodes_ranks=list()
    for block in collapsed:
        max_per_node=max_per_node_function(block)
        ranks=block['mpi_ranks']
        kj=ranks_to_nodes_ppn(max_per_node,ranks)
        nodes_ranks.extend(kj)
    return nodes_ranks

def merge_similar_ranks(self,ranks,can_merge_ranks_function):
    """!Given an array of JobRankSpec, merge any contiguous sequence of
    JobRankSpec objects where can_merge_ranks_function(rank1,rank2)
    returns true.      """
    if not isinstance(ranks,Sequence):
        raise TypeError('ranks argument must be a Sequence not a %s'%(
            type(ranks).__name__,))
    is_threaded=any([bool(rank.is_openmp()) for rank in ranks])
    i=0
    while i<len(ranks)-1:
        if can_merge_ranks_function(ranks[i],ranks[i+1]):
            ranks[i]=ranks[i].new_with(
                mpi_ranks=ranks[i]['mpi_ranks']+ranks[i+1]['mpi_ranks'])
            del ranks[i+1]
        else:
            i=i+1

def test():
    # MPI + OpenMP program test
    input1=[
        {'mpi_ranks':5, 'OMP_NUM_THREADS':12},
        {'mpi_ranks':7, 'OMP_NUM_THREADS':12},
        {'mpi_ranks':7} ]
    spec1=JobResourceSpec(input1)
    assert(spec1.has_threads())
    assert(spec1.total_ranks()==19)
    assert(not spec1.is_pure_serial())
    assert(not spec1.is_pure_openmp())
    assert(len(spec1)==3)
    for x in [0,1,2]:
        assert(spec1[x].is_mpi())
    for x in [0,1]:
        assert(spec1[x].is_openmp())
    assert(not spec1[2].is_openmp())
    for x in [0,1,2]:
        assert(not spec1[x].is_pure_serial())

    # Serial program test
    input2=[ { 'exe':'echo', 'args':['hello','world'] } ]
    spec2=JobResourceSpec(input2)
    assert(not spec2.has_threads())
    assert(spec2.total_ranks()==0)
    assert(spec2.is_pure_serial())
    assert(not spec2.is_pure_openmp())
    assert(spec2[0].is_pure_serial())
    assert(not spec2[0].is_openmp())
    assert(not spec2[0].is_mpi())

    # Pure openmp test
    input3=[ { 'OMP_NUM_THREADS':20 } ]
    spec3=JobResourceSpec(input3)
    assert(spec3.has_threads())
    assert(spec3.total_ranks()==0)
    assert(not spec3.is_pure_serial())
    assert(spec3.is_pure_openmp())
    assert(not spec3[0].is_pure_serial())
    assert(spec3[0].is_openmp())
    assert(not spec3[0].is_mpi())
