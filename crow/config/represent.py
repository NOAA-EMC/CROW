"""!Internal representation classes for crow.config.  These handle the
embedded yaml calculations, as well as internal representations of all
custom data types in the yaml files.  

\note Advanced python concepts in use.

To develop or understand this file, you must be fluent in the
following Python concepts:

 * operator overloading
 * custom dict/list types (eg. MutableMapping and MutableSequence)
 * python built-in eval() function    """

import logging
from collections import namedtuple, OrderedDict
from collections.abc import MutableMapping, MutableSequence
from copy import copy,deepcopy
from crow.config.exceptions import *

__all__=[ 'MISSING', 'dict_eval', 'list_eval', 'strcalc', 'Action',
          'Platform', 'Template', 'TaskStateAnd', 'TaskStateOr',
          'TaskStateNot', 'TaskStateIs', 'Taskable', 'Task',
          'Family','CycleAt','CycleTime','Cycle','Conditional',
          'calc','Trigger','Depend','Timespec', 'max_index', 'expand',
          'min_index', 'last_true', 'first_true', 'Eval' ]

logger=logging.getLogger('crow.represent')

## @var MISSING
# A special constant that indicates an argument was not specified.
MISSING=object()

class multidict(MutableMapping):
    """!This is a dict-like object that makes multiple dicts act as one.
    Its methods look over the dicts in order, returning the result
    from the first dict that has a matching key.  This class is
    intended to be used in favor of a new dict, when the underlying
    dicts have special behaviors that are lost upon copy to a standard dict."""
    def __init__(self,*args):
        self.__dicts=list(args)
        self.__keys=frozenset().union(*args)
    def __len__(self):            return len(self.__keys)
    def __contains__(self,k):     return k in self.__keys
    def __copy__(self):           return multidict(self.__dicts)
    def __setitem__(self,k,v):    raise NotImplementedError('immutable')
    def __delitem__(self,k):      raise NotImplementedError('immutable')
    def _globals(self):
        """!Returns the global values used in eval() functions"""
        return self.dicts[0]._globals()
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
        """!Returns the raw value of the given key without calling eval()"""
        for d in self.__dicts:
            if key in d:
                return d._raw(key)
        raise KeyError(key)
    def _has_raw(self,key):
        try:
            self._raw(key)
            return True
        except KeyError: return False
    def __repr__(self):
        return '%s(%s)'%(
            type(self).__name__,
            ','.join([repr(d) for d in self.__dicts]))

########################################################################

class dict_eval(MutableMapping):
    """!This is a dict-like object that knows how to eval() its contents,
    passing this dict as the local arguments.  This allows one to
    store actions like the following:

    * \c a = b + c

    where a, b, and c are elements of dict_eval.  The result of
    __getitem__(a) is then the result of:

    * __getitem__(b) + __getitem__(c)    """

    def __init__(self,child):
        assert(not isinstance(child,dict_eval))
        self.__child=copy(child)
        self.__cache=copy(child)
        self.__globals={}
    def __len__(self):          return len(self.__child)
    def _raw(self,key):
        """!Returns the value for the given key, without calling eval() on it"""
        return self.__child[key]
    def _has_raw(self,key):
        return key in self.__child
    def __contains__(self,k):   return k in self.__child
    def _globals(self):
        """!Returns the global values used in eval() functions"""
        return self.__globals
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
        """!Validates this dict_eval using its embedded Template object, if present """
        if 'Template' in self:
            self.Template._check_scope(self)
    def __getitem__(self,key):
        val=self.__cache[key]
        if hasattr(val,'_result'):
            val=from_config(key,val,self.__globals,self)
            self.__cache[key]=val
        return val
    def __getattr__(self,name):
        if name in self: return self[name]
        raise AttributeError(name)
    def _to_py(self,recurse=True):
        """!Converts to a python core object; does not work for cyclic object trees"""
        cls=type(self.__child)
        return cls([(k, to_py(v)) for k,v in self.items()])
    def _child(self): return self.__child
    def _recursively_set_globals(self,globals):
        """Recurses through the object tree setting the globals for eval() calls"""
        assert('tools' in globals)
        assert('doc' in globals)
        if self.__globals is globals: return
        self.__globals=globals
        for k,v in self.__child.items():
            try:
                v._recursively_set_globals(globals)
            except AttributeError: pass
    def __repr__(self):
        return '%s(%s)'%(type(self).__name__,repr(self.__child),)

########################################################################

class list_eval(MutableSequence):
    """!This is a dict-like object that knows how to eval() its contents,
    passing a containing dict as the local arguments.  The parent
    dict-like object is passed as the locals argument of the
    constructor.  This class allows one to store actions like the
    following:

    * \c a = [ b+c, b-c ]

    where a, b, and c are elements of the parent dict.  The result of
    __getitem__(a) is then the result of:

    \code
    [ self.__locals.__getitem__(b) + self.__locals.__getitem__(c),
      self.__locals.__getitem__(b) - self.__locals.__getitem__(c) ]
    \endcode    """
    def __init__(self,child,locals):
        self.__child=list(child)
        self.__cache=list(child)
        self.__locals=locals
        self.__globals={}
    def __len__(self):          return len(self.__child)
    def _raw(self,i):           
        """!Returns the value at index i without calling eval() on it"""
        return self.__child[i]
    def _has_raw(self,i):
        return i>=0 and len(self.__child)>i
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
        if hasattr(val,'_result'):
            val=from_config(index,val,self.__globals,self.__locals)
            self.__cache[index]=val
        return val
    def _to_py(self,recurse=True):
        """!Converts to a python core object; does not work for cyclic object trees"""
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

class expand(str):
    """!Represents a literal format string."""
    def _result(self,globals,locals):
        return eval('f'+repr(self),globals,locals)

class strcalc(str):
    """Represents a string that should be run through eval()"""
    def __repr__(self):
        return '%s(%s)'%(type(self).__name__,
                         super().__repr__())
    def _result(self,globals,locals):
        return eval(self,globals,locals)

class Eval(dict_eval):
    def _result(self,globals,locals):
        if 'result' not in self:
            raise EvalMissingCalc('"!Eval" block lacks a "result: !calc"')
        return self.result

def from_config(key,val,globals,locals):
    """!Converts s strcalc cor Conditional to another data type via eval().
    Other types are returned unmodified."""
    try:
        if hasattr(val,'_result'):
            return from_config(key,val._result(globals,locals),
                               globals,locals)
        return val
    except(KeyError,NameError,IndexError,AttributeError) as ke:
        raise CalcKeyError('%s: !%s %s -- %s %s'%(
            str(key),type(val).__name__,repr(val),type(ke).__name__,str(ke)))
    except RecursionError as re:
        raise CalcRecursionTooDeep('%s: !%s %s'%(
            str(key),type(val).__name__,str(val)))

def as_state(obj):
    """!Converts the containing object to a State.  Action objects are
    compared to the "complete" state."""
    if isinstance(obj,Action):       return State(other,'complete',True)
    elif isinstance(obj,State):      return obj
    elif isinstance(obj,ComboState): return obj
    else:                            return NotImplemented

class Action(dict_eval):
    """!Represents an action that a workflow should take, such as running
    a batch job."""
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

class Conditional(list_eval):
    def __init__(self,_index,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.__cache=MISSING
        self.__index=_index
    def _result(self,globals,locals):
        assert('tools' in globals)
        assert('doc' in globals)
        if self.__cache is MISSING:
            keys=list()
            values=list()
            for vk in self:
                if vk._has_raw('when') and vk._has_raw('do'):
                    values.append(vk._raw('do'))
                    keys.append(from_config('when',vk._raw('when'),
                        globals,multidict(vk,locals)))
                else:
                    raise ConditionalMissingDoWhen(
                        'Conditional list entries must have "do" and "when" '
                        'elements (saw keys: %s)'
                        %(', '.join(list(vk.keys())), ))
            index=self.__index(keys)
            if index is None:
                self.__cache=None
            else:
                try:
                    values=[ vk._raw('do') for vk in self ]
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
    """!Internal implementation of the YAML Template type.  Validates a
    dict_eval, inserting defaults and reporting errors via the
    TemplateErrors exception.    """
    def _check_scope(self,scope):
        checked=set()
        errors=list()
        template=dict(self)
        did_something=True

        # Main validation loop.  Iteratively validate, adding new
        # Templates as they become available via is_present.
        while did_something:
            did_something=False

            # Inner validation loop.  Validate based on all Templates
            # found thus far.  Add new templates if found via
            # is_present.
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

        # Insert default values for all templates found thus far:
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
    """!Used for constants that represent validation failure cases"""
    def __bool__(self):         return False

NOT_ALLOWED=TemplateValidationFailed()
TYPE_MISMATCH=TemplateValidationFailed()
UNKNOWN_TYPE=TemplateValidationFailed()

def validate_scalar(types,val,allowed,tname):
    """!Validates val against the type tname, and allowed values.  Forbids
    recursion (scalars cannot contain subobjects."""
    if allowed and val not in allowed:    return NOT_ALLOWED
    if len(types):                        return TYPE_MISMATCH
    for cls in TYPES[tname]:
        if isinstance(val,cls): return True
    return TYPE_MISMATCH

def validate_list(types,val,allowed,tname):
    """!Valdiates that val is a list that contains the specified allowed
    values.  Recurses into subobjects, which must be of type types[-1] """
    if not len(types):                     return TYPE_MISMATCH
    if str(type(val)) not in TYPES(tname): return UNKNOWN_TYPE
    for v in val:
        result=VALIDATORS[types[-1]](types[:-1],v,allowed,types[-1])
        if not result: return result
    return True

def validate_dict(types,val,allowed,typ):
    """!Valdiates that val is a map that contains the specified allowed
    values.  Recurses into subobjects, which must be of type types[-1] """
    if not len(types):                    return TYPE_MISMATCH
    if str(type(val)) not in typ['list']: return UNKNOWN_TYPE
    for k,v in val.items():
        result=VALIDATORS[types[-1]](types[:-1],v,allowed,types[-1])
        if not result: return result
    return True

## @var TYPES
# Mapping from YAML type to valid python types.
TYPES={ 'int':[int], 'bool':[bool], 'string':[str,bytes],
        'float':[float], 'list':[set,list,tuple,list_eval],
        'dict':[dict,dict_eval] }

## @var VALIDATORS
# Mapping from YAML type to validation function.
VALIDATORS={ 'map':validate_dict,     
             'seq':validate_list,
             'set':validate_list,
             'int':validate_scalar,
             'bool':validate_scalar,
             'string':validate_scalar,
             'float':validate_scalar }

def validate_type(var,typ,val,allowed):
    """!Top-level validation function.  Checks that the value val of the
    variable var is of the given type typ and has values in the list
    of those allowed.    """
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
    """!Main entry point to recursive validation system.  Validates
    variable var with value val against the YAML Template list item in
    scheme.    """
    if 'type' not in scheme:
        raise InvalidConfigTemplate(var+'.type: missing')
    typ=scheme.type
    if not isinstance(typ,str):
        raise InvalidConfigTemplate(var+'.type: must be a string')
    allowed=scheme.get('allowed',[])
    if not isinstance(allowed,list) and not isinstance(allowed,list_eval):
        raise InvalidConfigTemplate(var+'.allowed: must be a list')
    validate_type(var,typ,val,allowed)
