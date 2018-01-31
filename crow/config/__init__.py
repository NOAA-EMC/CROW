import yaml
from collections import Sequence, Mapping
import crow.tools
from .from_yaml import ConvertFromYAML
from .template import Template
from .represent import Action, Platform, ShellCommand
from .tools import CONFIG_TOOLS, ENV
from .tasks import Suite, Depend, AndDependency, SuitePath, \
    OrDependency, NotDependency, StateDependency, Dependable, \
    Taskable, Task, Family, Cycle, LogicalDependency, SuiteView, \
    RUNNING, COMPLETED, FAILED, TRUE_DEPENDENCY, FALSE_DEPENDENCY, \
    CycleExistsDependency, InputSlot, OutputSlot, EventDependency, \
    Event, DataEvent, ShellEvent
from .to_yaml import to_yaml
from .eval_tools import invalidate_cache
from .eval_tools import evaluate_immediates as _evaluate_immediates
from .exceptions import ConfigError, ConfigUserError

__all__=["from_string","from_file","to_py", 'Action', 'Platform', 'Template',
         'TaskStateAnd', 'TaskStateOr', 'TaskStateNot', 'TaskStateIs',
         'Taskable', 'Task', 'Family', 'CycleAt', 'CycleTime', 'Cycle',
         'Trigger', 'Depend', 'Timespec', 'SuitePath', 'ShellEvent', 'Event',
         'DataEvent', 'CycleExistsDependency', 'validate', 'EventDependency' ]

def to_py(obj):
    return obj._to_py() if hasattr(obj,'_to_py') else obj

def expand_text(text,scope):
    if hasattr(scope,'_expand_text'):
        return scope._expand_text(text)
    raise TypeError('In expand_text, the "scope" parameter must be an '
                    'object with the _expand_text argument.  You sent a '
                    '%s.'%(type(scope).__name__))

evaluate_immediates=_evaluate_immediates

def from_string(s,evaluate_immediates=True,validation_stage=None):
    if not s: raise TypeError('Cannot parse null string')
    c=ConvertFromYAML(yaml.load(s),CONFIG_TOOLS,ENV)
    result=c.convert(validation_stage=validation_stage)
    if evaluate_immediates:
        _evaluate_immediates(result,recurse=True)
    return result

def from_file(*args,evaluate_immediates=True,validation_stage=None):
    if not args: raise TypeError('Specify which files to read.')
    data=list()
    for file in args:
        with open(file,'rt') as fopen:
            data.append(fopen.read())
    return from_string(u'\n\n\n'.join(data),
                       evaluate_immediates=evaluate_immediates,
                       validation_stage=validation_stage)

def validate(obj,stage=''):
    if getattr(obj,'_validate'):
        obj._validate(stage)

def document_root(obj):
    return obj._globals()['doc']
