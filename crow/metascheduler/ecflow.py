import collections, datetime
from collections import OrderedDict

from io import StringIO

import crow.tools
from copy import copy
from crow.tools import to_timedelta, typecheck
from crow.metascheduler.simplify import simplify
from crow.config import SuiteView, Suite, Depend, LogicalDependency, \
          AndDependency, OrDependency, NotDependency, \
          StateDependency, Dependable, Taskable, Task, \
          Family, Cycle, RUNNING, COMPLETED, FAILED, \
          TRUE_DEPENDENCY, FALSE_DEPENDENCY, SuitePath, \
          CycleExistsDependency, invalidate_cache, EventDependency
__all__=['to_ecflow','ToEcflow']

f'This module requires python 3.6 or newer.'

ECFLOW_STATE_MAP={ COMPLETED:'complete',
                   RUNNING:'active',
                   FAILED:'aborted' }

def relative_path(start,dest):
    """Used to generate relative paths for ecflow.  Removes common
    path components and adds ".." components to go up one or more
    families, to re-express dest in a path relative to start."""
    if not start:
        raise ValueError('relative_path start path must be non-empty')
    if not dest:
        raise ValueError('relative_path destination path must be non-empty')
    i=0 # Index of first element that differs between start and dest lists
    while i<len(start) and i<len(dest) and start[i]==dest[i]:
        i+=1
    if i==len(start)-1 and len(start)==len(dest):
        # Destination task is in the same family as start:
        return f'./{dest[-1]}'
    if i==0:
        # No commonality.  Use absolute path.
        return '/' + '/'.join(dest)
    if len(start)-i-1>0:
        return '../'*(len(start)-i-1) + '/'.join(dest[i:])
    else:
        return './'+'/'.join(dest[i:])
    
def undate_path(relative_time,format,suite_path,undated):
    """!In dependencies within crow.config, the task paths have a
    timedelta at element 0 to indicate the relative time of the
    dependency.  This creates a new path, replacing the timedelta with
    a time string.  The format is sent to datetime.strftime."""
    assert(isinstance(undated,OrderedDict))
    if suite_path and hasattr(suite_path[0],'total_seconds'):
        when=relative_time+suite_path[0]
        result=[when.strftime(format)] + suite_path[1:]
        return result,True
    return suite_path,False

def remove_cyc_exist(task,dep,clock,undated):
    assert(isinstance(undated,OrderedDict))
    typecheck('dep',dep,LogicalDependency)
    if isinstance(dep,CycleExistsDependency):
        if dep.dt in clock:
            return TRUE_DEPENDENCY
        return FALSE_DEPENDENCY
    if isinstance(dep,AndDependency) or isinstance(dep,OrDependency):
        return type(dep)( *[
            remove_cyc_exist(task,d,clock,undated) for d in dep ])
    if isinstance(dep,NotDependency):
        return NotDependency(remove_cyc_exist(task,dep.depend,clock,undated))
    return dep

def convert_state_dep(fd,task,dep,clock,time_format,negate,undated):
    assert(isinstance(undated,OrderedDict))
    typecheck('clock',clock,crow.tools.Clock)
    task_path,did_undated=undate_path(clock.now,time_format,task.path,undated)
    dep_path,did_undated=undate_path(clock.now,time_format,dep.view.path,undated)
    rel_path=relative_path(task_path,dep_path)
    if did_undated and rel_path[0]=='/':
        undated[rel_path]=1
    state=ECFLOW_STATE_MAP[dep.state]
    fd.write(f'{rel_path} {"!=" if negate else "=="} {state}')

def convert_event_dep(fd,task,dep_path,event_name,clock,time_format,negate,undated):
    assert(isinstance(undated,OrderedDict))
    typecheck('clock',clock,crow.tools.Clock)
    task_path,did_undated=undate_path(clock.now,time_format,task.path,undated)
    dep_path,did_undated=undate_path(clock.now,time_format,dep_path,undated)
    rel_path=relative_path(task_path,dep_path)
    if did_undated and rel_path[0]=='/':
        undated[rel_path]=1
    fd.write(f'{rel_path}:{event_name}{" is clear" if negate else ""}')

def _convert_dep(fd,task,dep,clock,time_format,undated):
    assert(isinstance(undated,OrderedDict))
    first=True
    if isinstance(dep,OrDependency):
        for subdep in dep:
            if not first:
                fd.write(' or ')
            first=False
            _convert_dep(fd,task,subdep,clock,time_format,undated)
    elif isinstance(dep,AndDependency):
        for subdep in dep:
            if not first:
                fd.write(' and ')
            first=False
            _convert_dep(fd,task,subdep,clock,time_format,undated)
    elif isinstance(dep,NotDependency):
        fd.write('not ')
        if isinstance(dep.depend,StateDependency):
            convert_state_dep(fd,task,dep.depend,clock,time_format,True,
                              undated)
        elif isinstance(dep.depend,EventDependency):
            convert_event_dep(fd,task,dep.event.path[:-1],
                              dep.event.path[-1],clock,time_format,True,
                              undated)
        else:
            _convert_dep(fd,task,dep.depend,undated)
    elif isinstance(dep,StateDependency):
        convert_state_dep(fd,task,dep,clock,time_format,False,undated)
    elif isinstance(dep,EventDependency):
        convert_event_dep(fd,task,dep.event.path[:-1],
                          dep.event.path[-1],clock,time_format,False,undated)

def dep_to_ecflow(fd,task,dep,clock,time_format,undated):
    assert(isinstance(undated,OrderedDict))
    # Walk the tree, removing CycleExistsDependency objects:
    dep=remove_cyc_exist(task,dep,clock,undated)

    # Apply boolean algebra simplification algorithms.  This will
    # remove the true/false dependencies added by remove_cyc_exist.
    dep=simplify(dep)

    _convert_dep(fd,task,dep,clock,time_format,undated)

class ToEcflow(object):
    def __init__(self,suite):
        if not isinstance(suite,Suite):
            raise TypeError('The suite argument must be a Suite, '
                            'not a '+type(suite).__name__)

        try:
            scheduler=suite.ecFlow.scheduler
            clock=copy(suite.Clock)
        except(AttributeError,IndexError,TypeError,ValueError) as e:
            raise ValueError(
                'A Suite must define an ecFlow section containing '
                'scheduler, and suite_name; and the suite must have a Clock')

        update_globals={ 'sched':scheduler, 'to_ecflow':self, 'clock':clock }

        if 'parallelism' in suite.ecFlow:
            update_globals['parallelism']=suite.ecFlow.parallelism

        self.suite=suite
        self.suite.update_globals(**update_globals)
        self.settings=self.suite.ecFlow
        self.indent=self.settings.get('indent','  ')
        self.sched=scheduler
        self.clock=None
        self.undated=OrderedDict()

    ####################################################################
        
    # ecflow suite definition generation

    def _add_ecflow_def_meat(self,fd,node,indent):
        ecflow_def_more=node.get('ecflow_def','')
        if ecflow_def_more:
            for line in str(node.get('ecflow_def','')).splitlines():
                fd.write(f'{indent}{line.rstrip()}\n')
        if 'Trigger' in node:
            typecheck(node.task_path_var+'.Trigger',node.Trigger,
                      LogicalDependency,'!Depend')
            fd.write(f'{indent}trigger ')
            ecdep=dep_to_ecflow(
                fd,node,node.Trigger,
                self.suite.Clock,self.suite.ecFlow.suite_name,self.undated)
            fd.write('\n')
        if 'Complete' in node:
            typecheck(node.task_path_var+'.Complete',node.Complete,
                      LogicalDependency,'!Depend')
            fd.write(f'{indent}complete ')
            ecdep=dep_to_ecflow(
                fd,node,node.Complete,
                self.suite.Clock,self.suite.ecFlow.suite_name,self.undated)
            fd.write('\n')
        if 'Time' in node:
            typecheck(node.task_path_var+'.Time',node.Time,
                      datetime.timedelta,'!timedelta')
            dt=to_timedelta(node.Time)
            when=self.suite.Clock.now+dt
            #ecdate=when.strftime('%d.%m.%Y')
            ectime=when.strftime('%H:%M')
            fd.write(f'{indent}time {ectime}\n')
            #fd.write(f'{indent}date {ecdate}\n{indent}time {ectime}\n')
            
    def _make_task_def(self,fd,task):
        indent=max(0,len(task.path)-1)*self.indent
        fd.write(f'{indent}task {task.path[-1]}\n')
        event_number=1
        for item in task.child_iter():
            if item.is_event():
                fd.write(f'{indent} event {event_number} {item.path[-1]}\n')
                event_number+=1
        self._add_ecflow_def_meat(fd,task,indent+self.indent)
        fd.write(f'{indent}endtask\n')

    def _make_family_def(self,fd,family):
        indent=max(0,len(family.path)-1)*self.indent
        fd.write(f'{indent}family {family.path[-1]}\n')
        self._add_ecflow_def_meat(fd,family,indent+self.indent)
        for item in family.child_iter():
            if item.is_task():
                self._make_task_def(fd,item)
            elif item.is_family():
                self._make_family_def(fd,item)
        fd.write(f'{indent}endfamily\n')
    
    def _make_suite_def_for_one_cycle(self,fd):
        fd.write(f'suite {self.suite_name}\n')
        if 'ecflow_def' in self.suite:
            for line in self.suite.ecflow_def.splitlines():
                fd.write(f'{self.indent}{line.rstrip()}\n')
        for item in self.suite.child_iter():
            if item.is_task():
                self._make_task_def(fd,item)
            elif item.is_family():
                self._make_family_def(fd,item)
        fd.write('endsuite\n')

    def _make_externs(self,fd):
        for d in self.undated.keys():
            fd.write(f'extern {d}\n')

    ####################################################################

    # ecf file generation

    def _make_task_ecf_files(self,ecf_files,ecf_file_set,
                               ecf_file_path,task):
        ecf_file_set=task.get('ecf_file_set',ecf_file_set)
        ecf_file_path=ecf_file_path+[task.path[-1]]
        path_string='/'.join(ecf_file_path)
        print(f'task@{task.task_path_var} ecf file set {ecf_file_set} file {path_string}')
        if path_string in ecf_files[ecf_file_set]:
            return # This ecf file is already generated
        ecf_files[ecf_file_set][path_string]=task.ecf_file

    def _make_family_ecf_files(self,ecf_files,ecf_file_set,
                               ecf_file_path,family):
        ecf_file_set=family.get('ecf_file_set',ecf_file_set)
        ecf_file_path=ecf_file_path+[family.path[-1]]
        print(f'family@{family.task_path_var} ecf file set {ecf_file_set} file {ecf_file_path}')
        for t in family.child_iter():
            if t.is_task():
                self._make_task_ecf_files(
                    ecf_files,ecf_file_set,ecf_file_path,t)
            elif t.is_family():
                self._make_family_ecf_files(
                    ecf_files,ecf_file_set,ecf_file_path,t)

    def _make_ecf_files_for_one_cycle(self,ecf_files):
        ecf_file_set=self.settings.get('ecf_file_set','ecf_files')
        for t in self.suite.child_iter():
            if t.is_task():
                self._make_task_ecf_files(ecf_files,ecf_file_set,list(),t)
            elif t.is_family():
                self._make_family_ecf_files(ecf_files,ecf_file_set,list(),t)
        return ecf_files

    ####################################################################

    def to_ecflow(self):
        suite_def_files=dict()
        ecf_files=collections.defaultdict(dict)
        for clock in self.suite.Clock.iternow():
            invalidate_cache(self.suite,recurse=True)
            # Figure our where we are making the suite definition file:
            filename=clock.now.strftime(self.suite.ecFlow.suite_def_filename)
            if filename in suite_def_files:
                # We already processed a cycle whose suite definition
                # is the same as this one's.  Skip.
                continue
            self.suite_name=clock.now.strftime(self.suite.ecFlow.suite_name)
            with StringIO() as sio:
                self._make_suite_def_for_one_cycle(sio)
                suite_def_files[filename]=sio.getvalue()
            with StringIO() as sio:
                self._make_externs(sio)
                suite_def_files[filename]=sio.getvalue()+suite_def_files[filename]
            self._make_ecf_files_for_one_cycle(ecf_files)
        del self.suite
        return suite_def_files,ecf_files

def to_ecflow(suite):
    typecheck('suite',suite,Suite)
    return ToEcflow(suite).to_ecflow()
