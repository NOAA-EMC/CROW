import yaml
import crow.tools
from crow.config.from_yaml import ConvertFromYAML
from crow.config.template import Template
from crow.config.represent import Action, Platform, ShellCommand
from crow.config.tools import CONFIG_TOOLS, ENV
from crow.config.tasks import Suite, Depend, AndDependency, SuitePath, \
    OrDependency, NotDependency, StateDependency, Dependable, \
    Taskable, Task, Family, Cycle, LogicalDependency, SuiteView, \
    RUNNING, COMPLETED, FAILED, TRUE_DEPENDENCY, FALSE_DEPENDENCY, \
    CycleExistsDependency
from crow.config.to_yaml import to_yaml
from crow.config.eval_tools import invalidate_cache

__all__=["from_string","from_file","to_py", 'Action', 'Platform', 'Template',
         'TaskStateAnd', 'TaskStateOr', 'TaskStateNot', 'TaskStateIs',
         'Taskable', 'Task', 'Family', 'CycleAt', 'CycleTime', 'Cycle',
         'Trigger', 'Depend', 'Timespec', 'SuitePath', 
         'CycleExistsDependency']

def to_py(obj):
    return obj._to_py() if hasattr(obj,'_to_py') else obj

def expand_text(text,scope):
    if hasattr(scope,'_expand_text'):
        return scope._expand_text(text)
    raise TypeError('In expand_text, the "scope" parameter must be an '
                    'object with the _expand_text argument.  You sent a '
                    '%s.'%(type(scope).__name__))

def from_string(s):
    c=ConvertFromYAML(yaml.load(s),CONFIG_TOOLS,ENV)
    result=c.convert()
    #c.close()
    return result

def from_file(*args):
    data=list()
    for file in args:
        with open(file,'rt') as fopen:
            data.append(fopen.read())
    return from_string(u'\n\n\n'.join(data))
