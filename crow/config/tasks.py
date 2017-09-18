"""!Internal representation types for tasks and workflows

@note Basic python concepts in use

To develop or understand this file, you must be fluent in the
following basic Python concepts:

- namedtuple
- inheritance
"""

from functools import reduce
import operator
from datetime import timedelta
from abc import abstractmethod
from collections import namedtuple, OrderedDict, Sequence
from collections.abc import Mapping
from copy import copy, deepcopy
from crow.config.exceptions import *
from crow.config.eval_tools import dict_eval, strcalc, multidict
from crow.tools import to_timedelta, typecheck

__all__=[ 'SuiteView', 'Suite', 'Depend', 'LogicalDependency',
          'AndDependency', 'OrDependency', 'NotDependency',
          'StateDependency', 'Dependable', 'Taskable', 'Task',
          'Family', 'Cycle', 'RUNNING', 'COMPLETED', 'FAILED',
          'TRUE_DEPENDENCY', 'FALSE_DEPENDENCY', 'SuitePath',
          'CycleExistsDependency' ]

class StateConstant(object):
    def __init__(self,name):
        self.name=name
    def __repr__(self): return self.name
    def __str__(self): return self.name
RUNNING=StateConstant('RUNNING')
COMPLETED=StateConstant('COMPLETED')
FAILED=StateConstant('FAILED')

MISSING=object()
VALID_STATES=[ 'RUNNING', 'FAILED', 'COMPLETED' ]
ZERO_DT=timedelta()
EMPTY_DICT={}

class SuitePath(list):
    """!Simply a list that can be hashed."""
    def __hash__(self):
        result=0
        for element in self:
            result=result^hash(element)
        return result

class SuiteView(Mapping):
    LOCALS=set(['suite','viewed','path','parent','__cache','__globals',
                '_more_globals'])
    def __init__(self,suite,viewed,path,parent):
        # assert(isinstance(suite,Suite))
        # assert(isinstance(viewed,dict_eval))
        assert(isinstance(parent,SuiteView))
        self.suite=suite
        self.viewed=copy(viewed)
        self.viewed.task_path_list=path[1:]
        self.viewed.task_path_str='/'+'/'.join(path[1:])
        self.viewed.task_path_var='.'.join(path[1:])
        self.viewed.up=parent
        self.path=SuitePath(path)
        self.parent=parent
        self.__cache={}

    def __eq__(self,other):
        return self.path==other.path and self.suite is other.suite

    def __hash__(self):
        return hash(self.path)

    def has_cycle(self,dt):
        return CycleExistsDependency(to_timedelta(dt))

    def __len__(self):
        return len(self.viewed)

    def __iter__(self):
        for var in self.viewed: yield var

    def get_trigger_dep(self):
        return self.get('Trigger',TRUE_DEPENDENCY)

    def get_complete_dep(self):
        return self.get('Complete',FALSE_DEPENDENCY)

    def get_time_dep(self):
        return self.get('Time',timedelta.min)

    def child_iter(self):
        """!Iterates over all tasks and families that are direct 
        children of this family, yielding a SuiteView of each."""
        for var,val in self.items():
            if var=='up': continue
            if isinstance(val,SuiteView):
                yield val

    def walk_task_tree(self):
        """!Iterates over the entire tree of descendants below this SuiteView,
        yielding a SuiteView of each."""
        for var,val in self.items():
            if var=='up': continue
            if isinstance(val,SuiteView):
                yield val
                for t in val.walk_task_tree():
                    yield t

    def __contains__(self,key):
        return key in self.viewed

    def is_task(self): return isinstance(self.viewed,Task)

    def at(self,dt):
        dt=to_timedelta(dt)
        ret=SuiteView(self.suite,self.viewed,
                         [self.path[0]+dt]+self.path[1:],self)
        return ret

    def __getattr__(self,key):
        if key in SuiteView.LOCALS: raise AttributeError(key)
        if key in self: return self[key]
        raise AttributeError(key)

    def __getitem__(self,key):
        assert(isinstance(key,str))
        if key in self.__cache: return self.__cache[key]
        if key not in self.viewed: raise KeyError(key)
        val=self.viewed[key]

        if isinstance(val,SuiteView):
            return val
        elif isinstance(val,Task) or isinstance(val,Family):
            val=self.__wrap(key,val)
        elif hasattr(val,'_as_dependency'):
            val=self.__wrap(key,val._as_dependency(
                self.viewed._globals(),self.parent,self.path))
        self.__cache[key]=val
        return val

    def __wrap(self,key,obj):
        if isinstance(obj,Taskable):
            # Add to path when recursing into a family or task
            return SuiteView(self.suite,obj,self.path+[key],self)
        if isinstance(obj,Cycle):
            # Reset path when we see a cycle
            return SuiteView(self.suite,obj,self.path[:1],self)
        return obj

    # Dependency handling.  When this SuiteView is wrapped around a
    # Task or Family, these operators will generate dependencies.

    def __and__(self,other):
        dep=as_dependency(other)
        if dep is NotImplemented: return dep
        return AndDependency(as_dependency(self),dep)
    def __or__(self,other):
        dep=as_dependency(other)
        if dep is NotImplemented: return dep
        return OrDependency(as_dependency(self),dep)
    def __invert__(self):
        return NotDependency(StateDependency(self,COMPLETED))
    def is_running(self):
        return StateDependency(self,RUNNING)
    def is_failed(self):
        return StateDependency(self,FAILED)
    def is_completed(self):
        return StateDependency(self,COMPLETED)

class Suite(SuiteView):
    def __init__(self,suite,more_globals=EMPTY_DICT):
        if not isinstance(suite,Cycle):
            raise TypeError('The top level of a suite must be a Cycle not '
                            'a %s.'%(type(suite).__name__,))
        viewed=deepcopy(suite)
        globals=dict(viewed._globals())
        assert(globals['tools'] is not None)
        globals.update(suite=self,
                       RUNNING=RUNNING,COMPLETED=COMPLETED,
                       FAILED=FAILED)
        self._more_globals=dict(more_globals)

        globals.update(self._more_globals)
        super().__init__(self,viewed,[ZERO_DT],self)
        viewed._recursively_set_globals(globals)
    def has_cycle(self,dt):
        return CycleExistsDependency(to_timedelta(dt))
    def make_empty_copy(self,more_globals=EMPTY_DICT):
        new_more_globals=copy(self._more_globals)
        new_more_globals.update(more_globals)
        suite_copy=deepcopy(self.viewed)
        return Suite(suite_copy,new_more_globals)

class Depend(str):
    def _as_dependency(self,globals,locals,path):
        try:
            result=eval(self,globals,locals)
            result=as_dependency(result,path)
            return result
        except(SyntaxError,TypeError,KeyError,NameError,IndexError,AttributeError) as ke:
            raise DependError(f'!Depend {self}: {ke}')

def as_dependency(obj,path=MISSING,state=COMPLETED):
    """!Converts the containing object to a State.  Action objects are
    compared to the "complete" state."""
    if isinstance(obj,SuiteView):
        return StateDependency(obj,state)
    if isinstance(obj,LogicalDependency):
        return obj
    raise TypeError(f'{type(obj).__name__} is not a valid type for a dependency')
    return NotImplemented

class LogicalDependency(object):
    def __invert__(self):          return NotDependency(self)
    def __contains__(self,dep):    return False
    def __and__(self,other):
        if other is FALSE_DEPENDENCY: return other
        if other is TRUE_DEPENDENCY: return self
        dep=as_dependency(other)
        if dep is NotImplemented: raise TypeError(other)
        return AndDependency(self,dep)
    def __or__(self,other):
        if other is TRUE_DEPENDENCY: return other
        if other is FALSE_DEPENDENCY: return self
        dep=as_dependency(other)
        if dep is NotImplemented: raise TypeError(other)
        return OrDependency(self,dep)
    @abstractmethod
    def copy_dependencies(self): pass

class AndDependency(LogicalDependency):
    def __init__(self,*args):
        if not args: raise ValueError('Tried to create an empty AndDependency')
        self.depends=list(args)
        for dep in self.depends:
            typecheck('Dependencies',dep,LogicalDependency)
    def __len__(self):     return len(self.depends)
    def __str__(self):     return '( '+' & '.join([str(r) for r in self])+' )'
    def __repr__(self):    return f'AndDependency({repr(self.depends)})'
    def __hash__(self):    return reduce(operator.xor,[hash(d) for d in self])
    def __contains__(self,dep):
        return dep in self.depends
    def __and__(self,other):
        if other is TRUE_DEPENDENCY: return self
        if other is FALSE_DEPENDENCY: return other
        if isinstance(other,AndDependency):
            return AndDependency(*(self.depends+other.depends))
        dep=as_dependency(other)
        if dep is NotImplemented: return dep
        return AndDependency(*(self.depends+[dep]))
    def __iter__(self):
        for dep in self.depends:
            yield dep
    def __eq__(self,other):
        return isinstance(other,AndDependency) and self.depends==other.depends
    def copy_dependencies(self):
        return AndDependency(*[ dep.copy_dependencies() for dep in self ])

class OrDependency(LogicalDependency):
    def __init__(self,*args):
        if not args: raise ValueError('Tried to create an empty OrDependency')
        self.depends=list(args)
        for dep in self.depends:
            typecheck('A dependency',dep,LogicalDependency)
    def __str__(self):     return '( '+' | '.join([str(r) for r in self])+' )'
    def __repr__(self):    return f'OrDependency({repr(self.depends)})'
    def __len__(self):     return len(self.depends)
    def __hash__(self):    return reduce(operator.xor,[hash(d) for d in self])
    def __contains__(self,dep):
        return dep in self.depends
    def __or__(self,other):
        if other is FALSE_DEPENDENCY: return self
        if other is TRUE_DEPENDENCY: return other
        if isinstance(other,OrDependency):
            return OrDependency(*(self.depends+other.depends))
        dep=as_dependency(other)
        if dep is NotImplemented: return dep
        return OrDependency(*(self.depends+[dep]))
    def __iter__(self):
        for dep in self.depends:
            yield dep
    def __eq__(self,other):
        return isinstance(other,OrDependency) and self.depends==other.depends
    def copy_dependencies(self):
        return OrDependency(*[ dep.copy_dependencies() for dep in self ])

class NotDependency(LogicalDependency):
    def __init__(self,depend):
        typecheck('A dependency',depend,LogicalDependency)
        self.depend=depend
    def __invert__(self):        return self.depend
    def __str__(self):           return f'~ {self.depend}'
    def __repr__(self):          return f'NotDependency({repr(self.depend)})'
    def __iter__(self):          yield self.depend
    def __hash__(self):          return hash(self.depend)
    def __contains__(self,dep):  return self.depend==dep
    def __eq__(self,other):
        return isinstance(other,NotDependency) and self.depend==other.depend
    def copy_dependencies(self):
        return NotDependency(self.depend.copy_dependencies())

class CycleExistsDependency(LogicalDependency):
    def __init__(self,dt):
        self.dt=dt
    def __repr__(self):
        return f'cycle_exists({self.dt})'
    def __eq__(self,other):
        return isinstance(other,CycleExistsDependency) and self.dt==other.dt
    def __hash__(self): return hash(self.dt)
    def copy_dependencies(self):
        return CycleExistsDependency(self.dt)

class StateDependency(LogicalDependency):
    def __init__(self,view,state):
        self.view=view
        self.state=state
    @property
    def path(self):              return self.view.path
    def is_task(self):           return self.view.is_task()
    def __hash__(self):          return hash(self.view.path)^hash(self.state)
    def copy_dependencies(self): return StateDependency(self.view,self.state)
    def __repr__(self):
        return f'/{"/".join([str(s) for s in self.view.path])}'\
               f'= {self.state}'
    def __eq__(self,other):
        return isinstance(other,StateDependency) \
            and other.state==self.state \
            and other.view.path==self.view.path

class TrueDependency(LogicalDependency):
    def __and__(self,other):
        return other
    def __or__(self,other):
        return self
    def __invert__(self):
        return FALSE_DEPENDENCY
    def __eq__(self,other):
        return isinstance(other,TrueDependency)
    def __hash__(self): return 1
    def __copy__(self): return TRUE_DEPENDENCY
    def __deepcopy__(self): return TRUE_DEPENDENCY
    def copy_dependencies(self): return TRUE_DEPENDENCY
    def __repr__(self): return 'TRUE_DEPENDENCY'
    def __str__(self): return 'TRUE'

class FalseDependency(LogicalDependency):
    def __and__(self,other):
        return self
    def __or__(self,other):
        return other
    def __invert__(self):
        return TRUE_DEPENDENCY
    def __eq__(self,other):
        return isinstance(other,FalseDependency)
    def __hash__(self): return 0
    def __copy__(self): return FALSE_DEPENDENCY
    def __deepcopy__(self): return FALSE_DEPENDENCY
    def copy_dependencies(self): return FALSE_DEPENDENCY
    def __repr__(self): return 'FALSE_DEPENDENCY'
    def __str__(self): return 'FALSE'

TRUE_DEPENDENCY=TrueDependency()
FALSE_DEPENDENCY=FalseDependency()

class Dependable(dict_eval): pass
class Taskable(Dependable): pass
class Task(Taskable): pass
class Family(Taskable): pass
class Cycle(dict_eval): pass

class TaskArray(Taskable):
    def __init__(self,*args,**kwargs):
        super().init(*args,**kwargs)
        Index=self['Index']
        varname=Index[0]
        if not isinstance(varname,str):
            raise TypeError('Index first argument should be a string variable '
                            'name not a %s'%(type(varname.__name__),))
        values=Index[1]
        if not isinstance(values,Sequence):
            raise TypeError('Index second argument should be a sequence '
                            'name not a %s'%(type(values.__name__),))
        self.__instances=[MISSING]*len(values)
    @property
    def index_name(self):
        return self['Index'][0]
    @property
    def index_count(self):
        return len(self['Index'][1])
    def index_keys(self):
        keys=self['Index'][1]
        for k in keys: yield k
    def index_items(self):
        varname=self.index_name
        keys=self['Index'][1]
        for i in len(keys):
            yield keys[i],self.__for_index(i,varname,key)
    def for_index(self,i):
        if self.__instances[i] is not MISSING:
            return self.__instances[i]
        varname=self.index_name
        keys=self['Index'][1]
        return self.__for_index(i,varname,key)
    def __for_index(self,i,varname,key):
        the_copy=Family(self._raw_child())
        the_copy[varname]=key



