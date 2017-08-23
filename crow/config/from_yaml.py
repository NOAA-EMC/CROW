"""!Converts YAML objects to internal representations.

\note Advanced python concept in use.

You will not understand this file unless you are fluent in the
following python concept:

* Lexical functions

"""

from datetime import timedelta
from collections import namedtuple, OrderedDict
import re

import yaml
from yaml import YAMLObject

from crow.config.eval_tools import *
from crow.config.represent import *
from crow.config.tasks import *
from crow.config.template import Template
from crow.config.exceptions import *
from crow.tools import to_timedelta

__all__=['ConvertFromYAML']

# YAML representation objects:
class PlatformYAML(YAMLObject):   yaml_tag=u'!Platform'
class ActionYAML(YAMLObject):     yaml_tag=u'!Action'
class TemplateYAML(YAMLObject):   yaml_tag=u'!Template'

class FirstMaxYAML(list):         yaml_tag=u'!FirstMax'
class FirstMinYAML(list):         yaml_tag=u'!FirstMin'
class FirstTrueYAML(list):        yaml_tag=u'!FirstTrue'
class LastTrueYAML(list):         yaml_tag=u'!LastTrue'

class EvalYAML(dict): pass
class TaskYAML(OrderedDict): pass
class FamilyYAML(OrderedDict): pass
class CycleYAML(OrderedDict): pass

# Mapping from YAML representation class to a pair:
# * internal representation class
# * python core class for intermediate conversion
TYPE_MAP={ PlatformYAML: [ Platform, dict ], 
           TemplateYAML: [ Template, dict ],
           ActionYAML:   [ Action,   dict ],
           TaskYAML:     [ Task,     OrderedDict ],
           CycleYAML:    [ Cycle,    OrderedDict ],
           FamilyYAML:   [ Family,   OrderedDict ]
         }

def type_for(t):
    """!Returns an empty, internal representation, class for the given
    YAML type.  This is simply a wrapper around TYPE_MAP"""
    (internal_class,python_class)=TYPE_MAP[type(t)]
    return internal_class(python_class())

########################################################################

def timedelta_constructor(loader,node):
    s=loader.construct_scalar(node)
    return to_timedelta(s)

ZERO_DT=timedelta()

def timedelta_representer(dumper,dt):
    pre=''
    if dt<ZERO_DT:
        dt=abs(dt)
        pre='-'
    hours=dt.seconds//3600
    minutes=(dt.seconds-hours*3600)//60
    seconds=dt.seconds-hours*3600-minute*60
    rep=''
    if dt.days: rep=f'{dt.days}d'
    rep+=f'{hours:02d}:{minutes:02d}:{seconds:02d}'
    if dt.microseconds: rep+=f'.{dt.microseconds:06d}'
    return dumper.represent_scalar('!timedelta',rep)

yaml.add_representer(timedelta,timedelta_representer)
yaml.add_constructor('!timedelta',timedelta_constructor)

########################################################################

def add_yaml_string(key,cls):
    """!Generates and registers representers and constructors for custom
    string YAML types    """
    def representer(dumper,data):
        return dumper.represent_scalar(key,str(data))
    yaml.add_representer(cls,representer)
    def constructor(loader,node):
        return cls(loader.construct_scalar(node))
    yaml.add_constructor(key,constructor)

add_yaml_string(u'!expand',expand)
add_yaml_string(u'!calc',calc)
add_yaml_string(u'!Depend',Depend)

########################################################################

def add_yaml_sequence(key,cls): 
    """!Generates and registers representers and constructors for custom
    YAML sequence types    """
    def representer(dumper,data):
        return dumper.represent_sequence(key,data)
    def constructor(loader,node):
        return cls(loader.construct_sequence(node))
    yaml.add_representer(cls,representer)
    yaml.add_constructor(key,constructor)

add_yaml_sequence(u'!FirstMax',FirstMaxYAML)
add_yaml_sequence(u'!FirstMin',FirstMinYAML)
add_yaml_sequence(u'!LastTrue',LastTrueYAML)
add_yaml_sequence(u'!FirstTrue',FirstTrueYAML)

## @var CONDITIONALS
# Used to handle custom yaml conditional types.  Maps from conditional type
# to the function that performs the comparison.
CONDITIONALS={ FirstMaxYAML:max_index,
               FirstMinYAML:min_index,
               FirstTrueYAML:first_true,
               LastTrueYAML:last_true }

########################################################################

def add_yaml_ordered_dict(key,cls):
    """!Generates and registers representers and constructors for custom
    YAML map types    """
    def representer(dumper,data):
        return dumper.represent_ordered_dict(key,data)
    def constructor(loader,node):
        return cls(loader.construct_pairs(node))
    yaml.add_representer(cls,representer)
    yaml.add_constructor(key,constructor)

add_yaml_ordered_dict(u'!Eval',EvalYAML)
add_yaml_ordered_dict(u'!Cycle',CycleYAML)
add_yaml_ordered_dict(u'!Task',TaskYAML)
add_yaml_ordered_dict(u'!Family',FamilyYAML)

SUITE={ EvalYAML: Eval,
        CycleYAML: Cycle,
        TaskYAML: Task,
        FamilyYAML: Family }

########################################################################

def valid_name(varname):
    """!Returns true if and only if the variable name is supported by this implementation."""
    return not varname.startswith('_')     and '-' not in varname and \
           not varname.endswith('_yaml')   and '.' not in varname and \
           not varname.startswith('yaml_')

class ConvertFromYAML(object):
    def __init__(self,tree,tools,ENV):
        self.memo=dict()
        self.result=None
        self.tree=tree
        self.tools=tools
        self.validatable=dict()
        self.ENV=ENV

    def convert(self):
        self.result=self.from_dict(self.tree)
        globals={ 'tools':self.tools, 'doc':self.result, 'ENV': self.ENV }
        self.result._recursively_set_globals(globals)
        for i,v in self.validatable.items():
            v._validate()
        return self.result

    def to_eval(self,v,locals):
        """!Converts the object v to an internal implementation class.  If the
        conversion has already happened, returns the converted object
        from self.memo        """
        if id(v) not in self.memo:
            self.memo[id(v)]=self.to_eval_impl(v,locals)
        return self.memo[id(v)]

    def to_eval_impl(self,v,locals):
        """!Unconditionally converts the object v to an internal
        implementation class, without checking self.memo."""
        top=self.result
        # Specialized containers:
        cls=type(v)
        if cls in CONDITIONALS:
            return Conditional(CONDITIONALS[cls],
                               self.from_list(v,locals),locals)
        elif cls in SUITE:
            return self.from_dict(v,SUITE[cls])
        elif cls is EvalYAML:
            return Eval(self.from_dict(v))

        elif isinstance(v,list) and v and isinstance(v[0],tuple) \
             or isinstance(v,OrderedDict):
            return self.from_ordered_dict(v,GenericOrderedDict)
        # Generic containers:
        elif isinstance(v,YAMLObject): return self.from_yaml(v)
        elif isinstance(v,dict):     return self.from_dict(v)
        elif isinstance(v,list):     return self.from_list(v,locals)
        elif isinstance(v,set):      return set(self.from_list(v,locals))
        elif isinstance(v,tuple):    return self.from_list(v,locals)

        # Scalar types;
        return v

    def from_yaml(self,yobj):
        """!Converts a YAMLObject instance yobj of a YAML, and its elements,
        to internal implementation types.  Elements with unsupported
        names are ignored.        """
        ret=type_for(yobj)
        for k in dir(yobj):
            if not valid_name(k): continue
            ret[k]=self.to_eval(getattr(yobj,k),ret)
        self.validatable[id(ret)]=ret
        return ret

    def from_ordered_dict(self,tree,cls=GenericOrderedDict):
        top=self.result
        ret=cls(OrderedDict())
        for k,v in tree:
            if not valid_name(k): continue
            ret[k]=self.to_eval(v,ret)
        self.validatable[id(ret)]=ret
        return ret

    def from_dict(self,tree,cls=GenericDict):
        """!Converts an object yobj of a YAML standard map type, and its
        elements, to internal implementation types.  Elements with
        unsupported names are ignored.        """
        top=self.result
        ret=cls(tree)
        for k,v in tree.items():
            if not valid_name(k): continue
            ret[k]=self.to_eval(v,ret)
        return ret

    def from_list(self,sequence,locals,cls=GenericList):
        """!Converts an object yobj of a YAML standard sequence type, and its
        elements, to internal implementation types.  Elements with
        unsupported names are ignored.  This is also used to handle
        other sequence-like types such as omap or set.        """
        return cls(
            [self.to_eval(s,locals) for s in sequence],
            locals)
