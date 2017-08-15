"""!Internal representation classes for crow.config.  These handle the
embedded yaml calculations, as well as internal representations of all
custom data types in the yaml files."""

from crow.config.exceptions import *
from crow.config.eval_tools import list_eval, dict_eval, multidict, from_config, strcalc

__all__=[ 'Action','Platform', 'Conditional', 'calc','max_index',
          'min_index', 'last_true', 'first_true' ]

########################################################################

class Action(dict_eval):
    """!Represents an action that a workflow should take, such as running
    a batch job."""

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
