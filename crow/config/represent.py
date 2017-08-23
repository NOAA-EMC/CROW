"""!Internal representation classes for crow.config.  These handle the
embedded yaml calculations, as well as internal representations of all
custom data types in the yaml files."""

import re, abc
from datetime import timedelta
from copy import deepcopy
from crow.config.exceptions import *
from crow.config.eval_tools import list_eval, dict_eval, multidict, from_config, strcalc
from crow.tools import to_timedelta

__all__=[ 'Action','Platform', 'Conditional', 'calc','FirstMin',
          'FirstMax', 'LastTrue', 'FirstTrue', 'GenericList',
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
    def __init__(self,*args):
        super().__init__(*args)
        self.__result=Conditional.MISSING
    def _result(self,globals,locals):
        assert('tools' in globals)
        assert('doc' in globals)
        if self.__result is Conditional.MISSING:
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
            index=self._index(keys)
            if index is None:
                self.__result=None
            else:
                try:
                    values=[ vk._raw('do') for vk in self ]
                except AttributeError:
                    values=[ vk.value for vk in self ]
                    scope[var]=tmpl['default']
                self.__result=values[index]
        return self.__result
    def _deepcopy_privates_from(self,memo,other):
        super()._deepcopy_privates_from(memo,other)
        if other.__result is Conditional.MISSING:
            self.__result=Conditional.MISSING
        else:
            self.__result=deepcopy(other.__result,memo)

    @abc.abstractmethod
    def _index(lst): pass

class FirstMax(Conditional):
    def _index(self,lst):
        return lst.index(max(lst)) if lst else None

class FirstMin(Conditional):
    def _index(self,lst):
        return lst.index(min(lst)) if lst else None

class LastTrue(Conditional):
    def _index(self,lst):
        for i in range(len(lst)-1,-1,-1):
            if lst[i]: return i
        return None

class FirstTrue(Conditional):
    def _index(self,lst):
        for i in range(len(lst)):
            if lst[i]: return i
        return None

class calc(strcalc): pass
