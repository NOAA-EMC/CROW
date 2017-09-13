import yaml

from yaml.nodes import MappingNode, ScalarNode, SequenceNode

from collections import OrderedDict

from crow.config.eval_tools import *
from crow.config.represent import *
from crow.config.tasks import *
from crow.config.template import Template
from crow.config.exceptions import *
from crow.tools import to_timedelta

# We need to run the from_yaml module first, to initialize the yaml
# representers for some types.  This module does not actually use any
# symbols from from_yaml; only execution of that module is needed.
import crow.config.from_yaml

def to_yaml(yml):
    simple=dict([ (k,v) for k,v in yml._raw_cache().items() ])
    #print('INPUT: '+repr(simple))
    result=yaml.dump(simple)
    #print('OUTPUT: '+result)
    return result

########################################################################

def add_yaml_list_eval(key,cls): 
    def representer(dumper,data):
        if key is None:
            return dumper.represent_data(data._raw_child())
        else:
            return dumper.represent_sequence(key,data._raw_child())
    yaml.add_representer(cls,representer)

add_yaml_list_eval(u'!FirstMax',FirstMax)
add_yaml_list_eval(u'!FirstMin',FirstMin)
add_yaml_list_eval(u'!LastTrue',LastTrue)
add_yaml_list_eval(u'!FirstTrue',FirstTrue)
add_yaml_list_eval(u'!Immediate',Immediate)
add_yaml_list_eval(None,GenericList)

########################################################################

def add_yaml_dict_eval(key,cls): 
    """!Generates and registers a representer for a custom YAML mapping
    type    """
    def representer(dumper,data):
        if key is None:
            return dumper.represent_data(data._raw_child())
        else:
            return dumper.represent_mapping(key,data._raw_child())
    yaml.add_representer(cls,representer)

add_yaml_dict_eval(None,GenericDict)
add_yaml_dict_eval(u'!Platform',Platform)
add_yaml_dict_eval(u'!Action',Action)
add_yaml_dict_eval(u'!Template',Template)
add_yaml_dict_eval(u'!Eval',Eval)

########################################################################

def represent_ordered_mapping(dumper, tag, mapping, flow_style=None):
    value = []
    node = MappingNode(tag, value, flow_style=flow_style)
    if dumper.alias_key is not None:
        dumper.represented_objects[dumper.alias_key] = node
    best_style = True
    if hasattr(mapping, 'items'):
        mapping = list(mapping.items())
    for item_key, item_value in mapping:
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)
        if not (isinstance(node_key, ScalarNode) and not node_key.style):
            best_style = False
        if not (isinstance(node_value, ScalarNode) and not node_value.style):
            best_style = False
        value.append((node_key, node_value))
    if flow_style is None:
        if dumper.default_flow_style is not None:
            node.flow_style = dumper.default_flow_style
        else:
            node.flow_style = best_style
    return node

def add_yaml_OrderedDict_eval(key,cls): 
    """!Generates and registers a representer for a custom YAML mapping
    type    """
    def representer(dumper,data):
        simple=data._raw_cache()
        if not isinstance(simple,OrderedDict):
            simple=OrderedDict([ (k,v) for k,v in simple.items() ])
        return represent_ordered_mapping(dumper,key,simple)
    yaml.add_representer(cls,representer)

add_yaml_OrderedDict_eval(u'!Task',Task)
add_yaml_OrderedDict_eval(u'!Family',Family)
add_yaml_OrderedDict_eval(u'!Cycle',Cycle)

########################################################################

def represent_omap(dumper, mapping, flow_style=None):
    value = []
    tag = 'tag:yaml.org,2002:omap'

    node = SequenceNode(tag, value, flow_style=flow_style)

    if dumper.alias_key is not None:
        dumper.represented_objects[dumper.alias_key] = node
    best_style = True
    for item_key, item_value in mapping.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)
        subnode = MappingNode('tag:yaml.org,2002:map', [ ( node_key,node_value ) ])
        value.append(subnode)
    node.flow_style = True
    return node

yaml.add_representer(GenericOrderedDict,represent_omap)
