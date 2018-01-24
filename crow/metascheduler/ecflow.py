from io import StringIO
from crow.metascheduler.simplify import simplify
from crow.config import SuiteView, Suite, Depend, LogicalDependency, \
          AndDependency, OrDependency, NotDependency, \
          StateDependency, Dependable, Taskable, Task, \
          Family, Cycle, RUNNING, COMPLETED, FAILED, \
          TRUE_DEPENDENCY, FALSE_DEPENDENCY, SuitePath, \
          CycleExistsDependency
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
        return '/'+'/'.join(dest)
    return '../'*max(0,len(start)-i-1) + '/'.join(dest[i:])
    
def undate_path(relative_time,format,suite_path):
    """!In dependencies within crow.config, the task paths have a
    timedelta at element 0 to indicate the relative time of the
    dependency.  This creates a new path, replacing the timedelta with
    a time string.  The format is sent to datetime.strftime."""
    if suite_path and hasattr(suite_path[0],'total_seconds'):
        return [(suite_path[0]+relative_time).strftime(format)] + \
            suite_path[1:]
    return suite_path

def remove_cyc_exist(task,dep,clock):
    if isinstance(dep,CycleExistsDependency):
        if dep.dt in clock:
            return TRUE_DEPENDENCY
        return FALSE_DEPENDENCY
    if isinstance(dep,AndDependency) or isinstance(dep,OrDependency):
        return type(dep)( [
            remove_cyc_exist(task,d,clock) for d in dep ])
    if isinstance(dep,NotDependency):
        return NotDependency(remove_cyc_exist(task,dep.depend,clock))
    return dep

def convert_state_dep(sio,task,dep,clock,time_format,negate):
    task_path=undate_path(clock.now,time_format,task.path)
    dep_path=undate_path(clock.now,time_format,dep.view.path)
    rel_path=relative_path(task_path,dep_path)
    if len(rel_path)==1:
        path='./'+rel_path[0]
    else:
        path=rel_path.join('/')
    state=ECFLOW_STATE_MAP[dep.state]
    sio.write(f'{path} {"!=" if negate else "=="} {state}')

def convert_dep(sio,task,dep,clock,time_format):
    first=True
    if isinstance(dep,OrDependency):
        for subdep in dep:
            if not first:
                sio.write(' or ')
            first=False
            convert_dep(sio,task,subdep,clock,time_format)
    elif isinstance(dep,AndDependency):
        for subdep in dep:
            if not first:
                sio.write(' and ')
            first=False
            convert_dep(sio,task,subdep,clock,time_format)
    elif isinstance(dep,NotDependency):
        sio.write('not ')
        if isinstance(dep.depend,StateDependency):
            convert_state_dep(sio,task,dep.depend,clock,time_format,True)
        else:
            convert_dep(sio,task,dep.depend)
    elif isinstance(dep,StateDependency):
        convert_state_dep(sio,task,dep.depend,clock,time_format,False)


def dep_to_ecflow(task,dep,clock):
    # Walk the tree, removing CycleExistsDependency objects:
    dep=remove_cyc_exist(task,dep,clock)

    # Apply boolean algebra simplification algorithms.  This will
    # remove the true/false dependencies added by remove_cyc_exist.
    dep=simplify(dep)

    sio=StringIO()
    _convert_dep(sio,task,dep)
    ret=sio.getvalue()
    sio.close()
    return ret

class ToEcflow(object):
    def __init__(self,suite):
        if not isinstance(suite,Suite):
            raise TypeError('The suite argument must be a Suite, '
                            'not a '+type(suite).__name__)

        try:
            suite_path=suite.ecFlow.suite_path
            scheduler=suite.ecFlow.scheduler
            parallelism=suite.ecFlow.parallelism
            def_cycles=suite.ecFlow.def_cycles
        except(AttributeError,IndexError,TypeError,ValueError) as e:
            raise ValueError(
                'A Suite must define an ecFlow section containing: '
                'parallelism, scheduler, def_cycles, and suite_path')

        self.suite=suite
        self.suite.update_globals(sched=scheduler,to_ecflow=self,
                                  runner=parallelism)
        self.settings=self.suite.ecFlow
        self.indent=self.settings.get('indent','  ')
        self.sched=scheduler

    def _add_ecflow_def_meat(self,sio,task_or_family,indent):
        if 'ecflow_def' not in task_or_family:
            raise KeyError(
                f'{task_or_family.task_path_var}: In an ecFlow suite '
                'definition, all tasks and families must have an "ecflow_'
                'def" key whose value evaluates to the ecflow suite '
                'definition entry for that task or family.')
        for line in str(task_or_family.ecflow_def).splitlines():
            sio.write(f'{indent}{line.rstrip()}\n')

    def _make_task_def(self,sio,task):
        indent=max(0,len(family.path)-2)*self.indent
        sio.write(f'{indent}task {task.path[-1]}\n')
        self._add_ecflow_def_meat(sio,task,indent+self.indent)
        sio.write(f'{indent}end task\n')

    def _make_family_def(self,sio,family):
        indent=max(0,len(family.path)-2)*self.indent
        sio.write(f'{indent}family {family.path[-1]}\n')
        self._add_ecflow_def_meat(sio,family,indent+self.indent)
        for t in self.suite:
            if t.is_task(): self._make_task_def(sio,t)
            elif t.is_family(): self._make_family_def(sio,t)
        sio.write(f'{indent}end family\n')
    
    def make_suite_def(self):
        sio=StringIO()
        for t in self.suite.child_iter():
            if t.is_task(): self._make_task_def(sio,t)
            elif t.is_family(): self._make_family_def(sio,t)
        ret=sio.getvalue()
        sio.close()
        return ret
