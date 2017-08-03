from collections import namedtuple, OrderedDict
from collections.abc import MutableMapping, MutableSequence
from copy import copy,deepcopy
from crow.config.exceptions import *

__all__=[ 'MISSING', 'dict_eval', 'list_eval', 'strcalc', 'Action',
          'Platform', 'Template', 'TaskStateAnd', 'TaskStateOr',
          'TaskStateNot', 'TaskStateIs', 'Taskable', 'Task',
          'Family','CycleAt','CycleTime','Cycle','Conditional',
          'calc','Trigger','Depend','Timespec', 'max_index',
          'min_index', 'last_true', 'first_true' ]

MISSING=object()

class multidict(MutableMapping):
    def __init__(self,*args):
        self.__dicts=list(args)
        self.__keys=frozenset().union(*args)
    def __len__(self):            return len(self.__keys)
    def __contains__(self,k):     return k in self.__keys
    def __copy__(self):           return multidict(self.__dicts)
    def __setitem__(self,k,v):    raise NotImplementedError('immutable')
    def __delitem__(self,k):      raise NotImplementedError('immutable')
    def _globals(self):           return self.dicts[0]._globals()
    def __contains__(self,key):
        for d in self.__dicts:
            if key in d:
                return True
        return False
    def __iter__(self):
        for k in self.__keys: yield k
    def __getitem__(self,key):
        for d in self.__dicts:
            if key in d:
                return d[key]
        raise KeyError(key)
    def _raw(self,key):
        for d in self.__dicts:
            if key in d:
                return d._raw(key)
        raise KeyError(key)
    def __repr__(self):
        return '%s(%s)'%(
            type(self).__name__,
            ','.join([repr(d) for d in self.__dicts]))

########################################################################

class dict_eval(MutableMapping):
    def __init__(self,child):
        self.__child=copy(child)
        self.__cache=copy(child)
        self.__globals={}
    def __len__(self):          return len(self.__child)
    def _raw(self,key):         return self.__child[key]
    def __contains__(self,k):   return k in self.__child
    def _globals(self):         return self.__globals
    def __copy__(self):
        return dict_eval(self.__child)
    def __deepcopy__(self,memo):
        cls=type(self.__child)
        r=dict_eval(cls([ (k,deepcopy(v)) for k,v in self.__child]))
        memo[id(self)]=r
        return r
    def __setitem__(self,k,v):  
        self.__child[k]=v
        self.__cache[k]=v
    def __delitem__(self,k): del(self.__child[k], self.__cache[k])
    def __iter__(self):
        for k in self.__child.keys(): yield k
    def _validate(self):
        assert(self.__globals)
        if 'Template' in self:
            self.Template._check_scope(self)
    def __getitem__(self,key):
        val=self.__cache[key]
        if isinstance(val,strcalc) or isinstance(val,Conditional):
            val=from_config(key,val,self.__globals,self)
            self.__cache[key]=val
        return val
    def __getattr__(self,name):
        return self[name]
    def _to_py(self,recurse=True):
        cls=type(self.__child)
        return cls([(k, to_py(v)) for k,v in self.items()])
    def _child(self): return self.__child
    def _recursively_set_globals(self,globals):
        assert('tools' in globals)
        if self.__globals is globals: return
        self.__globals=globals
        for k,v in self.__child.items():
            if isinstance(v,dict_eval) or isinstance(v,list_eval):
                v._recursively_set_globals(globals)
    def __repr__(self):
        return '%s(%s)'%(type(self).__name__,repr(self.__child),)

########################################################################

class list_eval(MutableSequence):
    def __init__(self,child,locals):
        self.__child=list(child)
        self.__cache=list(child)
        self.__locals=locals
        self.__globals={}
    def __len__(self):          return len(self.__child)
    def _raw(self,i):           return self.__child[i]
    def __copy__(self):
        return list_eval(self.__child,self.__locals)
    def __deepcopy__(self,memo):
        r=list_eval([ deepcopy(v) for v in self.__child ],
                    deepcopy(self.__locals))
        memo[id(self)]=r
        return r
    def __setitem__(self,k,v):
        self.__child[k]=v
        self.__cache[k]=v
    def __delitem__(self,k):
        del(self.__child[k], self.__cache[k])
    def insert(self,i,o):
        self.__child.insert(i,o)
        self.__cache.insert(i,o)
    def __getitem__(self,index):
        val=self.__cache[index]
        if isinstance(val,strcalc) or isinstance(val,Conditional):
            val=from_config(index,val,self.__globals,self.__locals)
            self.__cache[index]=val
        return val
    def _to_py(self,recurse=True):
        return [ to_py(v) for v in self ]
    def _recursively_set_globals(self,globals):
        if self.__globals is globals: return
        self.__globals=globals
        for v in self.__child:
            if isinstance(v,dict_eval) or isinstance(v,list_eval):
                v._recursively_set_globals(globals)
    def __repr__(self):
        return '%s(%s)'%(type(self).__name__,repr(self.__child),)

########################################################################

class strcalc(str):
    def __repr__(self):
        return '%s(%s)'%(type(self).__name__,
                         super().__repr__())

def from_config(key,val,globals,locals):
    assert('tools' in globals)
    assert('tools' not in locals)
    assert(globals['tools'] is not None)
    try:
        if isinstance(val,strcalc):
            return eval(val,globals,locals)
        elif isinstance(val,Conditional):
            newval=val._result(globals,locals)
            return from_config(key,newval,globals,locals)
    except(KeyError,NameError,IndexError,AttributeError) as ke:
        raise CalcKeyError('%s: !%s %s -- %s %s'%(
            str(key),type(val).__name__,str(val),type(ke).__name__,str(ke)))
    except RecursionError as re:
        raise CalcRecursionTooDeep('%s: !%s %s'%(
            str(key),type(val).__name__,str(val)))
    return val


def as_state(obj):
    if isinstance(obj,Action):       return State(other,'complete',True)
    elif isinstance(obj,State):      return obj
    elif isinstance(obj,ComboState): return obj
    else:                            return NotImplemented

class Action(dict_eval):
    def __and__(self,other):
        other=as_state(other)
        if other is NotImplemented: return other
        return ComboState('and',as_state(self),other)
    def __or__(self,other):
        other=as_state(other)
        if other is NotImplemented: return other
        return ComboState('or',as_state(self),other)
    def __not__(self):
        return State(self,'complete',False)

class Platform(dict_eval): pass

class TaskStateAnd(namedtuple('TaskStateAnd',['task1','task2'])): pass
class TaskStateOr(namedtuple('TaskStateOr',['task1','task2'])): pass
class TaskStateNot(namedtuple('TaskStateNot',['task'])): pass
class TaskStateIs(namedtuple('TaskStateIs',['task','state'])): pass

def as_task_state(obj,state='COMPLETED'):
    if type(obj) in [ TaskStateAnd, TaskStateOr, TaskStateNot, TaskStateIs ]:
        return obj
    if isinstance(obj,Taskable):
        return TaskStateIs(obj,state)
    return NotImplemented

class Taskable(object):
    def __init__(self,info):
        self.info=info
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

class Task(Taskable): pass
class Family(Taskable): pass
class CycleAt(namedtuple('CycleAt',['cycle','hours','days'])): pass
class CycleTime(namedtuple('CycleTime',['cycle','hours','days'])): pass
class Cycle(Taskable):
    def name(self,when):
        return self.info.get('format','cyc_%Y%m%d_%H%M%S')
    def at(self,hours=0,days=0):
        return CycleAt(self,hours,days)
    def clock(self,hours=0,days=0):
        return CycleTime(self,hours,days)

class Conditional(list_eval):
    def __init__(self,_index,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.__cache=MISSING
        self.__index=_index
    def _result(self,globals,locals):
        assert('tools' in globals)
        if self.__cache is MISSING:
            keys=list()
            values=list()
            for vk in self:
                value=vk._raw('value')
                values.append(value)
                keys.append(from_config('key',vk._raw('key'),globals,
                    multidict(vk,locals)))
            index=self.__index(keys)
            if index is None:
                self.__cache=None
            else:
                try:
                    values=[ vk._raw('value') for vk in self ]
                except AttributeError:
                    values=[ vk.value for vk in self ]
                    scope[var]=tmpl['default']
                self.__cache=values[index]
        return self.__cache

def max_index(lst): return lst.index(max(lst)) if lst else None
def min_index(lst): return lst.index(min(lst)) if lst else None

def last_true(lst):
    for i in range(len(lst)-1,-1,-1):
        if lst[i]: return i
    return None
def first_true(lst):
    for i in range(len(lst)):
        if lst[i]: return i
    return None

class calc(strcalc): pass
class Trigger(strcalc): pass
class Depend(strcalc): pass
class Timespec(strcalc): pass

########################################################################

# Validation
class Template(dict_eval):
    def _check_scope(self,scope):
        checked=set()
        errors=list()
        template=dict(self)
        did_something=True
        while did_something:
            did_something=False
            for var in set(scope)-checked:
                if var not in template: continue
                try:
                    did_something=True
                    checked.add(var)
                    scheme=template[var]
                    validate_var(scheme,var,scope[var])
                    if 'if_present' in scheme:
                        ip=from_config(
                            var,scheme._raw('if_present'),self._globals(),scope)
                        if not ip: continue
                        new_template=dict(ip)
                        new_template.update(template)
                        template=new_template
                except ConfigError as ce:
                    errors.append(ce)
                    raise
        for var in template:
            if var not in scope:
                tmpl=template[var]
                if 'default' in tmpl:
                    try:
                        did_something=True
                        scope[var]=tmpl._raw('default')
                    except AttributeError:
                        scope[var]=tmpl['default']

        if errors: raise TemplateErrors(errors)

class TemplateValidationFailed(object):
    def __bool__(self):         return False
NOT_ALLOWED=TemplateValidationFailed()
TYPE_MISMATCH=TemplateValidationFailed()
UNKNOWN_TYPE=TemplateValidationFailed()

def validate_scalar(types,val,allowed,tname):
    if allowed and val not in allowed:    return NOT_ALLOWED
    if len(types):                        return TYPE_MISMATCH
    for cls in TYPES[tname]:
        if isinstance(val,cls): return True
    return TYPE_MISMATCH

def validate_list(types,val,allowed,tname):
    if not len(types):                     return TYPE_MISMATCH
    if str(type(val)) not in TYPES(tname): return UNKNOWN_TYPE
    for v in val:
        result=VALIDATORS[types[-1]](types[:-1],v,allowed,types[-1])
        if not result: return result
    return True

def validate_dict(types,val,allowed,typ):
    if not len(types):                    return TYPE_MISMATCH
    if str(type(val)) not in typ['list']: return UNKNOWN_TYPE
    for k,v in val.items():
        result=VALIDATORS[types[-1]](types[:-1],v,allowed,types[-1])
        if not result: return result
    return True

TYPES={ 'int':[int], 'bool':[bool], 'string':[str,bytes],
        'float':[float], 'list':[set,list,tuple,list_eval],
        'dict':[dict,dict_eval] }

VALIDATORS={ 'map':validate_dict,     
             'seq':validate_list,
             'set':validate_list,
             'int':validate_scalar,
             'bool':validate_scalar,
             'string':validate_scalar,
             'float':validate_scalar }

def validate_type(var,typ,val,allowed):
    types=typ.split()
    for t in types:
        if t not in VALIDATORS:
            raise InvalidConfigType('%=%s: unknown type in %s'%(
                str(var),repr(t),repr(typ)))
    result=VALIDATORS[types[-1]](types[:-1],val,allowed,types[-1])
    if result is UNKNOWN_TYPE:
        raise InvalidConfigType('%s: type %s: unknown type in %s'%(
            str(var),repr(t),repr(typ)))
    elif result is TYPE_MISMATCH:
        raise InvalidConfigValue('%s=%s: not valid for type %s'%(
            str(var),repr(val),repr(typ)))
    elif result is NOT_ALLOWED:
        raise InvalidConfigValue('%s=%s: not an allowed value (%s)'%(
            str(var),repr(val),', '.join([repr(s) for s in allowed])))

def validate_var(scheme,var,val):
    if 'type' not in scheme:
        raise InvalidConfigTemplate(var+'.type: missing')
    typ=scheme.type
    if not isinstance(typ,str):
        raise InvalidConfigTemplate(var+'.type: must be a string')
    allowed=scheme.get('allowed',[])
    if not isinstance(allowed,list) and not isinstance(allowed,list_eval):
        raise InvalidConfigTemplate(var+'.allowed: must be a list')
    validate_type(var,typ,val,allowed)
