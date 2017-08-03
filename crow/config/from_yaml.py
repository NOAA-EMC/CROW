from collections import namedtuple, OrderedDict
import yaml
from yaml import YAMLObject
from crow.config.represent import *

__all__=['ConvertFromYAML']

# YAML representation objects:
class PlatformYAML(YAMLObject):   yaml_tag=u'!Platform'
class ActionYAML(YAMLObject):     yaml_tag=u'!Action'
class TemplateYAML(YAMLObject):   yaml_tag=u'!Template'
class MaxKeyYAML(list): pass
class MinKeyYAML(list): pass
class FirstTrueYAML(list): pass
class LastTrueYAML(list): pass
class TaskYAML(OrderedDict): pass
class FamilyYAML(OrderedDict): pass
class CycleYAML(OrderedDict): pass

TYPE_MAP={ PlatformYAML: [ Platform, dict ], 
           TemplateYAML: [ Template, dict ],
           ActionYAML:   [ Action,   dict ],
           TaskYAML:     [ Task,     OrderedDict ],
           CycleYAML:    [ Cycle,    OrderedDict ],
           FamilyYAML:   [ Family,   OrderedDict ]
         }

def type_for(t):
    (internal_class,python_class)=TYPE_MAP[type(t)]
    return internal_class(python_class())

def add_yaml_string(key,cls):
    def representer(dumper,data):
        return dumper.represent_scalar(key,str(data))
    yaml.add_representer(cls,representer)
    def constructor(loader,node):
        return cls(loader.construct_scalar(node))
    yaml.add_constructor(key,constructor)

add_yaml_string(u'!calc',calc)
add_yaml_string(u'!Trigger',Trigger)
add_yaml_string(u'!Depend',Depend)
add_yaml_string(u'!Timespec',Timespec)

########################################################################

def add_yaml_sequence(key,cls):
    def representer(dumper,data):
        return dumper.represent_sequence(key,data)
    def constructor(loader,node):
        return cls(loader.construct_sequence(node))
    yaml.add_representer(cls,representer)
    yaml.add_constructor(key,constructor)

add_yaml_sequence(u'!MaxKey',MaxKeyYAML)
add_yaml_sequence(u'!MinKey',MinKeyYAML)
add_yaml_sequence(u'!LastTrue',LastTrueYAML)
add_yaml_sequence(u'!FirstTrue',FirstTrueYAML)

########################################################################

def add_yaml_ordered_dict(key,cls):
    def representer(dumper,data):
        return dumper.represent_ordered_dict(key,data)
    def constructor(loader,node):
        return cls(loader.construct_pairs(node))
    yaml.add_representer(cls,representer)
    yaml.add_constructor(key,constructor)

add_yaml_ordered_dict(u'!Cycle',CycleYAML)
add_yaml_ordered_dict(u'!Task',TaskYAML)
add_yaml_ordered_dict(u'!Family',FamilyYAML)

def valid_name(varname):
    return not varname.startswith('_')     and '-' not in varname and \
           not varname.endswith('_yaml')   and '.' not in varname and \
           not varname.startswith('yaml_')

class ConvertFromYAML(object):
    def __init__(self,tree,tools):
        self.memo=dict()
        self.result=None
        self.tree=tree
        self.tools=tools
        self.validatable=dict()

    def convert(self):
        self.result=self.from_dict(self.tree)
        globals={ 'tools':self.tools, 'doc':self.result }
        self.result._recursively_set_globals(globals)
        for i,v in self.validatable.items():
            v._validate()
        return self.result

    def to_eval(self,v,locals):
        if id(v) not in self.memo:
            self.memo[id(v)]=self.to_eval_impl(v,locals)
        return self.memo[id(v)]

    def to_eval_impl(self,v,locals):
        top=self.result
        # Specialized containers:
        cls=type(v)
        if cls in CONDITIONALS:
            return Conditional(CONDITIONALS[cls],
                               self.from_list(v,locals),locals)

        # Generic containers:
        elif isinstance(v,YAMLObject): return self.from_yaml(v)
        elif isinstance(v,dict):     return self.from_dict(v)
        elif isinstance(v,list):     return self.from_list(v,locals)
        elif isinstance(v,set):      return set(self.from_list(v,locals))
        elif isinstance(v,tuple):    return self.from_list(v,locals)

        # Scalar types;
        return v

    def from_yaml(self,yobj):
        ret=type_for(yobj)
        for k in dir(yobj):
            if not valid_name(k): continue
            ret[k]=self.to_eval(getattr(yobj,k),ret)
        self.validatable[id(ret)]=ret
        return ret

    def from_dict(self,tree):
        top=self.result
        ret=dict_eval(tree)
        for k,v in tree.items():
            if not valid_name(k): continue
            ret[k]=self.to_eval(v,ret)
        return ret

    def from_list(self,sequence,locals):
        return list_eval(
            [self.to_eval(s,locals) for s in sequence],
            locals)


CONDITIONALS={ MaxKeyYAML:max_index,
               MinKeyYAML:min_index,
               FirstTrueYAML:first_true,
               LastTrueYAML:last_true }
