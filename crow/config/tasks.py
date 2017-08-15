"""!Internal representation types for tasks and workflows

@note Basic python concepts in use

To develop or understand this file, you must be fluent in the
following basic Python concepts:

- namedtuple
- inheritance
"""

from collections import namedtuple, UserDict
from copy import copy
from crow.config.exceptions import *
from crow.config.eval_tools import dict_eval, strcalc

__all__=[ 'TaskStateAnd', 'TaskStateOr', 'Trigger', 'Depend',
          'TaskStateNot', 'TaskStateIs', 'Taskable', 'Task',
          'Family', 'CycleAt', 'CycleTime', 'Cycle', 'Timespec'  ]

class SuiteView(dict_eval):
    def __init__(self,path,child):
        super().__init__(child)
        self.__path=path

    @property
    def path(self): return self.__path

    def __getattr__(self,key):
        if key in self: return self[key]
        # Any key not "in self" is referring to an actual method or
        # property of the child class.  Hence, we pass it through
        # without __wrapping it.
        return getattr(self._raw_child(),key)

    def __wrap(self,obj):
        if isinstance(val,Taskable):
            # Add to path when we add a family
            return SuiteView(self.__path+[key],val)
        if isinstance(val,Cycle):
            # Reset path when we see a cycle
            return SuiteView(self.__path[:1],val)
        if isinstance(obj,SuiteView):
            return obj
        return val

    def __getitem__(self,key):
        return self.__wrap(dict_eval.__getitem__(self,key))

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
    """!Abstract base class that adds logical operators for dependency
    specification.  This is intended to be used as a mixin.  It must
    be included last in an inheritance list to ensure non-abstract
    class constructors are called.    """
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

class Task(dict_eval,Taskable): pass
class Family(dict_eval,Taskable): pass
class CycleAt(dict_eval,Taskable): pass
class CycleTime(namedtuple('CycleTime',['cycle','hours','days'])): pass
class Cycle(dict_eval):
    def name(self,when):
        return self.get('format','cyc_%Y%m%d_%H%M%S')
    def at(self,hours=0,days=0):
        return CycleAt(self,hours,days)
    def clock(self,hours=0,days=0):
        return CycleTime(self,hours,days)
