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
        self.specify_affinity=bool(settings.get('specify_affinity',True))
        self.specify_n_ranks=bool(settings.get('specify_n_ranks',True))
        self.indent_text=str(settings.get('indent_text','  '))
        self.specify_memory=bool(settings.get('specify_memory',True))
        self.use_task_geometry=bool(settings.get('use_task_geometry',True))
        #self.memory_type=str(settings.get('memory_type','batch')).lower()
        #if memory_type not in [ 'batch','compute','none']:
        #    raise ValueError(f'For an LSF scheduler, the memory_type must be "batch", "compute", or "none" (case-insensitive) not {settings["memory_type"]}')

    # ------------------------------------------------------------------

    def _decide_memory_for(self,spec):
        if spec[0].is_exclusive() and spec[0].get('batch_memory',''):
            return tools.memory_in_bytes(spec[0]['batch_memory'])
        elif not spec[0].is_exclusive() and spec[0].get('compute_memory',''):
            return tools.memory_in_bytes(spec[0]['compute_memory'])
        elif spec[0].get('memory',''):
            return tools.memory_in_bytes(spec[0]['memory'])
        else:
            return 2000*1048576.

    # ------------------------------------------------------------------

    def _ranks_affinity_and_span_for(self,spec):
        """Calculate ranks, affinity, and span for an LSF batch card to match
        a JobResourceSpec.  This is returned as a list of dicts with
        keys "ranks," "affinity," and "span."

        There are two different types of output depending on whether
        this is a compound request.
        
        Single request: ten nodes, four ranks per node, on a 28 core machine:

            #BSUB -R 'affinity[core(7)]'
            #BSUB -R 'span[ptile=4]'
            #BSUB -n 10
        
            ras=[ { 'ranks':40, 'affinity':'core(7)', 'span':'ptile=4' } ]

        Compound request: ten nodes, four ranks per node; and eight nodes,
        28 ranks per node; in one request, on a 28 core machine:

            #BSUB -R '10*{span[ptile=4]affinity[core(7)]} + 8*{span[ptile=28]affinity[core(1)]}'

            ras=[ { 'ranks':40, 'affinity':'core(7)', 'span':'ptile=4' },
                  { 'ranks':8,  'affinity':'core(1)', 'span':'ptile=28' }]
        """

        ras=[ ] # List of dict with keys: ranks, affinity, span

        for ranks in spec:
            ppn=self.nodes.max_ranks_per_node(ranks)
            mpi_ranks=max(1,int(ranks.get('mpi_ranks',1)))
            num_nodes=int(math.ceil(mpi_ranks/float(ppn)))
            span=f'ptile={min(mpi_ranks,ppn)}'

            if 'lsf_affinity' in ranks:
                affinity=ranks['lsf_affinity']
            else:
                hyperthreads=self.nodes.hyperthreads_for(ranks)
                max_affinity=self.nodes.cores_per_node
                affinity_type='core'
                if hyperthreads>1:
                    max_affinity*=self.nodes.cpus_per_core
                    affinity_type='cpu'
                affinity_count=max_affinity//ppn
                affinity=f'{affinity_type}({affinity_count})'
                
            ras.append( {
                'ranks':mpi_ranks, 'affinity':affinity, 'span':span })
        return ras
            
    # ------------------------------------------------------------------

    def _batch_stdout_stderr(self,spec,sio):
        if 'outerr' in spec:
            sio.write(f'#BSUB -o {spec["outerr"]}\n')
        else:
            if 'stdout' in spec:
                sio.write('#BSUB -o {spec["stdout"]}\n')
            if 'stderr' in spec:
                sio.write('#BSUB -e {spec["stderr"]}\n')

    # ------------------------------------------------------------------

    def max_ranks_per_node(self,spec):
        return max([ self.nodes.max_ranks_per_node(j) for j in spec ])

    ####################################################################

    # Generation of batch cards

    def batch_accounting(self,*args,**kwargs):
        spec=tools.make_dict_from(args,kwargs)
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
        self._batch_stdout_stderr(spec,sio)
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

        # ------------------------------------------------------------
        # Handle memory
        
        rusage=''
        if self.specify_memory:
            bytes=self._decide_memory_for(spec)
            megabytes=int(math.ceil(bytes/1048576.))
            rusage=f'rusage[mem={megabytes:d}]'

        # ------------------------------------------------------------
        # stdout/stderr locations
        
        self._batch_stdout_stderr(spec[0],sio)

        # ------------------------------------------------------------
        # ranks, affinity, and span

        if spec[0].exclusive:
            sio.write('#BSUB -x\n')

     
        if len(spec)==1:
            # Special case: only one block.  We'll put the affinity
            # and span on their own line and use "-n" to specify the
            # number of ranks.

            # There are some specialer cases in here, including pure
            # OpenMP or pure serial.
            
            ras=self._ranks_affinity_and_span_for(spec)
            
            if rusage:
                sio.write(f"""#BSUB -R '{rusage}'\n""")

            # Affinity is mandatory:
            sio.write(f"""#BSUB -R 'affinity[{ras[0]["affinity"]}]'\n""")

            # Span is only used when OpenMP or MPI are in use:
            if not spec.is_pure_serial():
                sio.write(f"""#BSUB -R 'span[{ras[0]["span"]}]'\n""")

            # -n is used except in shared, non-mpi jobs
            if spec[0].exclusive or spec.total_ranks()>2:
                sio.write(f"""#BSUB -n {ras[0]["ranks"]}\n""")

        elif not self.use_task_geometry:

            # General case: more than one block.  Task geometry is
            # disabled.
            
            hyperthreads=max([self.nodes.hyperthreads_for(r) for r in spec])
            node_size=self.nodes.cores_per_node
            if hyperthreads>1:
                node_size*=self.nodes.cpus_per_core
            max_ppn=min([self.nodes.max_ranks_per_node(r) for r in spec])
            affinity_count=node_size//max_ppn
            affinity_type='cpu' if hyperthreads>1 else 'core'
            affinity=f'{affinity_type}({affinity_count})'

            if rusage:
                sio.write(f"""#BSUB -R '{rusage}'\n""")
            sio.write(f"""#BSUB -R 'affinity[{affinity}]'\n""")
            sio.write(f"""#BSUB -R 'span[{min(spec.total_ranks(),max_ppn)}]'\n""")
            sio.write(f"""#BSUB -n {spec.total_ranks()}\n""")
            
        else:
            # General case: more than one block.  Task geometry is
            # enabled.
            ras=self._ranks_affinity_and_span_for(spec)
            sio.write("#BSUB -R '")
            first=True
            for ras1 in ras:
                if first:
                    first=False
                else:
                    sio.write(' + ')
                sio.write(f'{ras1["ranks"]}*'
                          f'{{span[{ras1["span"]}]'
                          f'affinity[{ras1["affinity"]}]{rusage}}}')
            sio.write("'\n")
            
        ret=sio.getvalue()
        sio.close()
        return ret

    ####################################################################

    # Generation of Rocoto XML

    def _rocoto_stdout_stderr(self,spec,indent,space,sio):
        if 'outerr' in spec:
            sio.write(f'{indent*space}<join>{spec["outerr"]}</join>\n')
        else:
            if 'stdout' in spec:
                sio.write('{indent*space}<stdout>{spec["stdout"]}</stdout>\n')
            if 'stderr' in spec:
                sio.write('{indent*space}<stderr>{spec["stderr"]}</stderr>\n')

    # ------------------------------------------------------------------
                
    def rocoto_accounting(self,*args,indent=0,**kwargs):
        spec=tools.make_dict_from(args,kwargs)
        space=self.indent_text
        sio=StringIO()
        if 'queue' in spec:
            sio.write(f'{indent*space}<queue>{spec["queue"]!s}</queue>\n')
        if 'account' in spec:
            sio.write(f'{indent*space}<account>{spec["account"]!s}</account>\n')
        if 'project' in spec:
            sio.write(f'{indent*space}<account>{spec["project"]!s}</account>\n')
        if 'account' in spec:
            sio.write(f'{indent*space}<account>{spec["account"]!s}</account>\n')
        if 'jobname' in spec:
            sio.write(f'{indent*space}<jobname>{spec["jobname"]!s}</jobname>\n')
        self._rocoto_stdout_stderr(spec,indent,space,sio)
        ret=sio.getvalue()
        sio.close()
        return ret

    # ------------------------------------------------------------------

    def rocoto_resources(self,spec,indent=0):
        sio=StringIO()
        space=self.indent_text
        if not isinstance(spec,JobResourceSpec):
            spec=JobResourceSpec(spec)

        if spec[0].get('walltime',''):
            dt=tools.to_timedelta(spec[0]['walltime'])
            dt=dt.total_seconds()
            hours=int(dt//3600)
            minutes=int((dt%3600)//60)
            seconds=int(math.floor(dt%60))
            sio.write(f'{indent*space}<walltime>{hours}:{minutes:02d}:{seconds:02d}</walltime>\n')
       
        # Handle memory.
        if self.specify_memory:
            bytes=self._decide_memory_for(spec)
            megabytes=int(math.ceil(bytes/1048576.))
            sio.write(f'{indent*space}<memory>{megabytes:d}M</memory>\n')

        # Stdout and stderr if specified:
        self._rocoto_stdout_stderr(spec[0],indent,space,sio)

        # Write nodes=x:ppn=y
        # Split into (nodes,ranks_per_node) pairs.  Ignore differing
        # executables between ranks while merging them (same_except_exe):
        nodes_ranks=self.nodes.to_nodes_ppn(
            spec,can_merge_ranks=self.nodes.same_except_exe)
        
        sio.write(indent*space+'<nodes>' \
            + '+'.join([f'{max(n,1)}:ppn={max(p,1)}' for n,p in nodes_ranks ]) \
            + '</nodes>\n')

        # Write out affinity.
        hyperthreads=max([self.nodes.hyperthreads_for(r) for r in spec])
        node_size=self.nodes.cores_per_node
        if hyperthreads>1:
            node_size*=self.nodes.cpus_per_core
        max_ppn=min([self.nodes.max_ranks_per_node(r) for r in spec])
        affinity_count=node_size//max_ppn
        affinity_type='cpu' if hyperthreads>1 else 'core'
        
        sio.write(f'{indent*space}<native>'
                  f"-R 'affinity[{affinity_type}({affinity_count})]'"
                  '</native>\n')
        #sio.write(f'{indent*space}<nodes>{requested_nodes}:ppn={nodesize}</nodes>')
        ret=sio.getvalue()
        sio.close()
        return ret

def test():
    settings={ 'physical_cores_per_node':28,
               'logical_cpus_per_core':2,
               'specify_memory':True,
               'use_task_geometry':False,
               'hyperthreading_allowed':True }
    sched=Scheduler(settings)

    # MPI + OpenMP program test
    input0=[ {'mpi_ranks':5, 'OMP_NUM_THREADS':12} ]
    spec1=JobResourceSpec(input0)
    result=sched.rocoto_resources(spec1)
    bresult=sched.batch_resources(spec1)
    #assert(result=='<nodes>6:ppn=2+1:ppn=7</nodes>\n')
    print(f'{input0} => \n{result}')
    print(f'{input0} => \n{bresult}')

    # Compound MPI + OpenMP program test
    input1=[
        {'mpi_ranks':5, 'OMP_NUM_THREADS':12},
        {'mpi_ranks':7, 'OMP_NUM_THREADS':12},
        {'mpi_ranks':7} ]
    spec1=JobResourceSpec(input1)
    result=sched.rocoto_resources(spec1)
    bresult=sched.batch_resources(spec1)
    #assert(result=='<nodes>6:ppn=2+1:ppn=7</nodes>\n')
    print(f'{input1} => \n{result}')
    print(f'{input1} => \n{bresult}')

    # Serial program test
    input2=[ { 'exe':'echo', 'args':['hello','world'], 'exclusive':False } ]
    spec2=JobResourceSpec(input2)
    result=sched.rocoto_resources(spec2)
    bresult=sched.batch_resources(spec2)
    #assert(result=='<cores>1</cores>\n')
    print(f'{input2} => \n{result}')
    print(f'{input2} => \n{bresult}')
    
    # Exclusive serial program test
    input3=[ { 'exe':'echo', 'args':['hello','world 2'], 'exclusive':True } ]
    spec3=JobResourceSpec(input3)
    result=sched.rocoto_resources(spec3)
    bresult=sched.batch_resources(spec3)
    #assert(result=='<nodes>1:ppn=2</nodes>\n')
    print(f'{input3} => \n{result}')
    print(f'{input3} => \n{bresult}')

    # Pure openmp test
    input4=[ { 'OMP_NUM_THREADS':20 } ]
    spec4=JobResourceSpec(input4)
    result=sched.rocoto_resources(spec4)
    bresult=sched.batch_resources(spec4)
    #assert(result=='<nodes>1:ppn=2</nodes>\n')
    print(f'{input4} => \n{result}')
    print(f'{input4} => \n{bresult}')

    # Too big for node
    try:
        input5=[ { 'OMP_NUM_THREADS':200, 'mpi_ranks':3 } ]
        spec5=JobResourceSpec(input5)
        result=sched.rocoto_resources(spec5)
        assert(False)
    except MachineTooSmallError:
        pass # success!

