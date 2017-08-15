"""!Internal representation types for tasks and workflows

@note Basic python concepts in use

To develop or understand this file, you must be fluent in the
following basic Python concepts:

- namedtuple
- inheritance
"""

from collections import namedtuple
from crow.config.exceptions import *
from crow.config.eval_tools import dict_eval, strcalc

__all__=[ 'TaskStateAnd', 'TaskStateOr', 'Trigger', 'Depend',
          'TaskStateNot', 'TaskStateIs', 'Taskable', 'Task',
          'Family', 'CycleAt', 'CycleTime', 'Cycle', 'Timespec'  ]

class Trigger(strcalc): pass
class Depend(strcalc): pass
class Timespec(strcalc): pass

def as_state(obj):
    """!Converts the containing object to a State.  Action objects are
    compared to the "complete" state."""
    if isinstance(obj,Action):       return State(other,'complete',True)
    elif isinstance(obj,State):      return obj
    elif isinstance(obj,ComboState): return obj
    else:                            return NotImplemented


class TaskStateAnd(namedtuple('TaskStateAnd',['task1','task2'])): pass
class TaskStateOr(namedtuple('TaskStateOr',['task1','task2'])): pass
class TaskStateNot(namedtuple('TaskStateNot',['task'])): pass
class TaskStateIs(namedtuple('TaskStateIs',['task','state'])): pass

def as_task_state(obj,state='COMPLETED'):
    """!Converts obj to a task state comparison.  If obj is not a task
    state, then it is compared to the specified state."""
    if type(obj) in [ TaskStateAnd, TaskStateOr, TaskStateNot, TaskStateIs ]:
        return obj
    if isinstance(obj,Taskable):
        return TaskStateIs(obj,state)
    return NotImplemented

class Taskable(object):
    """!Represents any noun in a dependency specification."""
    def __and__(self,other):
        other=as_task_state(other)
        if other is NotImplemented: return other
        return TaskStateAnd(as_task_state(self),other)
    def __or__(self,other):
        other=as_task_state(other)
        if other is NotImplemented: return other
        return TaskStateOr(as_task_state(self),other)
    def __not__(self): 
        return TaskStateNot(as_task_state(self))

class Task(dict_eval): pass
class Family(dict_eval): pass
class CycleAt(namedtuple('CycleAt',['cycle','hours','days'])): pass
class CycleTime(namedtuple('CycleTime',['cycle','hours','days'])): pass
class Cycle(dict_eval):
    def name(self,when):
        return self.get('format','cyc_%Y%m%d_%H%M%S')
    def at(self,hours=0,days=0):
        return CycleAt(self,hours,days)
    def clock(self,hours=0,days=0):
        return CycleTime(self,hours,days)
