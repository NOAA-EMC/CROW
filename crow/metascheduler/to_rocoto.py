from crow.config import Action, Template, TaskStateAnd, TaskStateOr, \
          TaskStateNot, TaskStateIs, Taskable, Task, \
          Family,CycleAt,CycleTime,Cycle,Trigger,Depend,Timespec
import sys
from io import StringIO as sio
from collections import namedtuple

__all__=['to_rocoto']

KEY_WARNINGS={ 'scheduler':'Did you mean rocoto_scheduler?',
               'cyclethrottle':'Did you mean cycle_throttle?' }

REQUIRED_KEYS={ 'workflow_install':'directory to receive Rocoto workflow',
                'rocoto_scheduler':'Rocoto internal scheduler class' }

class MetaschedulerConfigError(Exception): pass

class RocotoTask(namedtuple('RocotoTask',
        ['scope','task_path','trigger','complete'])):
    pass

def task_state_dep(task,time):
    attr='task="%s"'%(task,)
    if task.state != 'completed':
        attr+=' state="%s"'%(task.state.upper(),)
    if time:
        attr+=' cycle_offset="%s"'
    if state == 'completed':
        return '  '*depth + '<taskdep>%s</taskdep>\n'%(tree.task,)
    else:
        return '  '*depth +  \
            '<taskdep state="%s">%s</taskdep>\n'%(
                tree.task,tree.state.upper())

TO_ROCOTO_DEP={
    TaskStateAnd: lambda x,t: to_dep('<and>',[x.task1,x.task2]),
    TaskStateOr:  lambda x,t: to_dep('<or>',[x.task1,x.task2]),
    TaskStateNot: lambda x,t: to_dep('<not>',[x.task]),
    TaskStateIs:  task_state_dep,
    }

def merge_trigger(a,b):
    if a:
        if b:
            return TaskStateAnd(a,b)
        else:
            return a
    elif b:
        return b

def merge_time(a,b):
    if a is not None:
        if b is not None:
            return a if a>b else b
        else:
            return a
    elif b is not None:
        return b

def merge_deps(task,family_trigger,family_complete,family_time):
    ( trigger, complete, time ) = None, None, None
    if 'trigger' in task:           trigger  = task.trigger
    if 'complete' in task:          complete = task.complete
    if 'time' in task:              time     = task.time

    trigger=merge_trigger(trigger,family_trigger)
    complete=merge_trigger(complete,family_complete)
    time=merge_time(time,family_time)

    return trigger, complete, time

class ToRocoto(object):
    def __init__(self,suite):
        self.suite=suite
        self.tasks=dict()
        self.completes=dict()

    def validate_cycle(self):
        """!Perform sanity checks on top level of suite."""
        suite=self.suite
        if not isinstance(suite,Cycle):
            raise TypeError('The top level of a suite must be a Cycle, '
                            'not a %s'%(type(suite).__name__))

        for key,what in REQUIRED_KEYS.items():
            if key not in suite:
                raise KeyError('%s: missing variable (%s)'%(key,what))

        for key,what in KEY_WARNINGS.items():
            if key in suite:
                raise KeyError('%s: %s'%(key,what))

    def flatten_tasks(self,fd):
        suite=self.suite
        for name,task in suite.items():
            if isinstance(task,Task):
                self.convert_task([0,name],task,None,None,0)
            elif isinstance(task,Family):
                self.convert_task([0,name],task,None,None,0)

        if self.completes:
            self.handle_completes()

        for name,task in suite.items():
            if name == 'final': continue
            fd.write('''<task name="{name:%s}">
<command>{command:%s}</command>
<join><cyclestr>&WORKFLOW_INSTALL;/log/{logname:%s}</cyclestr></join>
''')

    def handle_completes(self):
        if [0,'final'] not in self.tasks:
            raise MetaschedulerConfigError(
                'In a Rocoto workflow, if a suite has "complete" '
                'directives, it must have a "final" task at the suite '
                '(cycle) level.')

        final=self.tasks[ [0,'final'] ]
        if final.trigger or final.complete:
            raise MetaschedulerConfigError(
                'In a Rocoto workflow, the "final" task must have no'
                '"complete" or "trigger" directives.')

    def add_tasks(self,tasks_path,task):
        for task in tasks:
            if 'complete' in task:
                self.completes[task_path]=task
            self.tasks[task_path]=task

    def top_level_xml(self):
        
        out.write('''<?xml version="1.0"?>
<!DOCTYPE workflow [
  <!ENTITY WORKFLOW_INSTALL "%s">
]>

<workflow realtime="F"
  scheduler="{rocoto_scheduler:%s}"
'''%(suite.workflow_install,
     suite.rocoto_scheduler,))
        if 'cycle_throttle' in suite:
            out.write('  cycle_throttle="{%d}"\n'%int(suite.cycle_throttle,10))
        out.write('>\n')
        out.write('''
  <log verbosity=10><cyclestr>&WORKFLOW_INSTALL;/logs/@Y@m@d@H.log</cyclestr></log>

  <cycledef>{start:%Y%m%d%H%M} {end:%Y%m%d%H%M} {step:%s}</cycledef>

'''.format({
    'start':datetime.datetime(suite.start),
    'end':datetime.datetime(suite.end),
    'step':to_hhmmss(int(suite.step,10))}))

    def bottom_xml(self):
        out.write('</workflow>\n')

    def convert_task(self,task_path,scope,family_trigger,
                     family_complete,family_time):
        ( trigger, complete, time ) = merge_deps(
            scope,family_trigger,family_complete,family_time)

        return RocotoTask(scope,task_path,trigger,complete)

    def convert_family(self,task_path,scope,family_trigger,
                       family_complete,family_time):
        ( trigger, complete, time ) = merge_deps(
            scope,family_trigger,family_complete,family_time)
        tasks=list()
        for name,task in scope.items():
            path=task_path+[name]
            if isinstance(task,Task):
                tasks.append(self.convert_task(path,task,trigger,complete))
            elif isinstance(task,Family):
                tasks.extend(self.convert_family(path,task,trigger,complete))

        return tasks

    
def to_rocoto(suite):
    tr=ToRocoto(suite)
    tr.validate_cycle()
    tr.flatten_tasks(sys.stdout)
