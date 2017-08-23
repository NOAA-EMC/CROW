"""!Internal representation classes for crow.config.  These handle the
embedded yaml calculations, as well as internal representations of all
custom data types in the yaml files."""

import re
from datetime import timedelta
from copy import deepcopy
from crow.config.exceptions import *
from crow.config.eval_tools import list_eval, dict_eval, multidict, from_config, strcalc
from crow.tools import to_timedelta

__all__=[ 'Action','Platform', 'Conditional', 'calc','max_index',
          'min_index', 'last_true', 'first_true', 'GenericList',
          'GenericDict', 'GenericOrderedDict' ]

########################################################################

class Action(dict_eval):
    """!Represents an action that a workflow should take, such as running
    a batch job."""

class GenericDict(dict_eval): pass
class GenericOrderedDict(dict_eval): pass
class GenericList(list_eval): pass
class Platform(dict_eval): pass

class Conditional(list_eval):
    MISSING=object()
    def __init__(self,_index,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.__cache=Conditional.MISSING
        self.__index=_index
    def _result(self,globals,locals):
        assert('tools' in globals)
        assert('doc' in globals)
        if self.__cache is Conditional.MISSING:
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
    def __deepcopy__(self,memo):
        cls=type(self)
        index=deepcopy(self.__index)
        child,locals=self._deepcopy_child_and_locals(memo)
        r=cls(index,child,locals)
        r._deepcopy_privates_from(memo,self)
        return r

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
