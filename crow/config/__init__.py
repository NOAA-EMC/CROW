import yaml
import crow.tools
from crow.config.from_yaml import ConvertFromYAML
from crow.config.represent import Action, Platform, Template, \
    TaskStateAnd, TaskStateOr, TaskStateNot, TaskStateIs, Taskable, \
    Task, Family, CycleAt, CycleTime, Cycle, Trigger, Depend, Timespec
from crow.config.tools import CONFIG_TOOLS

__all__=["from_string","from_file","to_py", 'Action', 'Platform', 'Template',
         'TaskStateAnd', 'TaskStateOr', 'TaskStateNot', 'TaskStateIs',
         'Taskable', 'Task', 'Family', 'CycleAt', 'CycleTime', 'Cycle',
         'Trigger', 'Depend', 'Timespec']

def to_py(obj):
    return obj._to_py() if hasattr(obj,'_to_py') else obj

def from_string(s):
    c=ConvertFromYAML(yaml.load(s),CONFIG_TOOLS)
    result=c.convert()
    #c.close()
    return result

def from_file(*args):
    data=list()
    for file in args:
        with open(file,'rt') as fopen:
            data.append(fopen.read())
    return from_string(u'\n\n\n'.join(data))
