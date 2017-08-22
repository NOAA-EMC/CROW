import sys
from datetime import timedelta, datetime
from io import StringIO as sio
from collections import namedtuple
from collections.abc import Sequence, Mapping
import crow.sysenv
from crow.config import SuiteView, Suite, Depend, LogicalDependency, \
          AndDependency, OrDependency, NotDependency, \
          StateDependency, Dependable, Taskable, Task, \
          Family, Cycle, RUNNING, COMPLETED, FAILED, \
          TRUE_DEPENDENCY, FALSE_DEPENDENCY, SuitePath, \
          CycleExistsDependency

__all__=['ToRocoto','RocotoConfigError']

KEY_WARNINGS={ 'cyclethrottle':'Did you mean cycle_throttle?' }

REQUIRED_KEYS={ 'workflow_install':'directory to receive Rocoto workflow',
                'scheduler':'Scheduler class',
                'workflow_xml': 'Contents of Rocoto XML file'}

class RocotoConfigError(Exception): pass

ROCOTO_STATE_MAP={ COMPLETED:'SUCCEEDED',
                   FAILED:'DEAD',
                   RUNNING:'RUNNING' }

ROCOTO_DEP_TAG={ AndDependency:'and',
                 OrDependency:'or',
                 NotDependency:'not' }

ZERO_DT=timedelta()

def cycle_offset(dt):
    sign=1
    if dt<ZERO_DT:
        dt=-dt
        sign=-1
    total=round(dt.total_seconds())
    hours=int(total//3600)
    minutes=int((total-hours*3600)//60)
    seconds=int(total-hours*3600-minutes*60)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

def to_rocoto_dep(dep,fd,indent):
    if type(dep) in ROCOTO_DEP_TAG:
        tag=ROCOTO_DEP_TAG[type(dep)]
        fd.write(f'{"  "*indent}<{tag}>\n')
        for d in dep: to_rocoto_dep(d,fd,indent+1)
        fd.write(f'{"  "*indent}</{tag}>\n')
    elif isinstance(dep,StateDependency):
        path='-'.join(dep.path[1:])
        state=ROCOTO_STATE_MAP[dep.state]
        tag='taskdep' if dep.is_task() else 'metataskdep'
        fd.write(f'{"  "*indent}<{tag} task="{path}" state="{state}"/>\n')
    elif isinstance(dep,CycleExistsDependency):
        dt=cycle_offset(dep.dt)
        fd.write(f'{"  "*indent}<cycleexistdep cycle_offset="{dt}"/>\n')

def to_rocoto_time_dep(dt,fd,indent):
    string_dt=cycle_offset(dt)
    fd.write(f'{"  "*indent}<timedep>{string_dt}</timedep>\n')

def to_rocoto_time(t):
    return t.strftime('%Y%m%d%H%M')

def xml_quote(s):
    return s.replace('&','&amp;') \
            .replace('"','&quot;') \
            .replace('<','&lt;')

class ToRocoto(object):
    def __init__(self,suite,fd):
        self.fd=fd
        if isinstance(suite,Cycle):
            suite=Suite(suite)
        elif not isinstance(suite,Suite):
            raise TypeError('The suite argument must be a Suite, '
                            'not a '+type(suite).__name__)
        
        # Get the Rocoto settings:
        if 'Rocoto' not in suite or not isinstance(suite.Rocoto,Mapping):
            raise RocotoConfigError(
                'To run a suite in Rocoto, you must have a suite-level '
                'Rocoto mapping that defines Rocoto-specific information.')
        self.settings=suite.Rocoto

        # Get the scheduler
        if 'scheduler' not in self.settings:
            raise RocotoConfigError(
                'The Rocoto section of a suite must specify the scheduler '
                'settings in the "scheduler" section.')

        scheduler_settings=self.settings.scheduler
        scheduler_name=self.settings.scheduler.name

        sched=crow.sysenv.get_scheduler(scheduler_name,scheduler_settings)

        self.suite=suite.make_empty_copy({'sched':sched})
        self.settings=self.suite.Rocoto
        self.__completes=dict()
        self.__families=set()
        self.__spacing=suite.Rocoto.get('indent_text','  ')
        if not isinstance(self.__spacing,str):
            raise TypeError("Suite's Rocoto.indent_text, if present, "
                            "must be a string.")
        self.__dummy_var_count=0

    def validate_cycle(self):
        """!Perform sanity checks on top level of suite."""
        settings=self.settings
        for key,what in REQUIRED_KEYS.items():
            if key not in settings:
                raise KeyError('%s: missing variable (%s)'%(key,what))

        for key,what in KEY_WARNINGS.items():
            if key in settings:
                raise KeyError('%s: %s'%(key,what))

    def convert_family(self,indent,view,trigger,complete,time):
        trigger=trigger & view.get_trigger_dep()
        complete=complete | view.get_complete_dep()
        time=max(time,view.get_time_dep())
        space=self.__spacing

        self.__dummy_var_count+=1
        dummy_var="dummy_var_"+str(self.__dummy_var_count)

        path=xml_quote('-'.join(view.path[1:]))
        if not isinstance(view,Suite):
            self.fd.write(f'''{space*indent}<metatask name="{path}">
{space*indent}  <var name="{dummy_var}">DUMMY_VALUE</var>
''')
        self.__families.add(SuitePath(view.path[1:-1]))

        for key,child in view.items():
            if not isinstance(child,SuiteView):
                continue
            if child.path[1:] == ['final']:
                if not child.is_task():
                    raise RocotoConfigError(
                        'The "final" task must be a Task, not a Family.')
                self.__final_task=child
            elif child.is_task():
                self.convert_task(indent+1,child,trigger,complete,time)
            else:
                self.convert_family(indent+1,child,trigger,complete,time)

        if not isinstance(view,Suite):
            self.fd.write(f'{space*indent}</metatask>\n')

    def convert_task(self,indent,view,trigger,complete,time):
        trigger=trigger & view.get_trigger_dep()
        complete=complete | view.get_complete_dep()
        time=max(time,view.get_time_dep())
        space=self.__spacing

        if complete is not FALSE_DEPENDENCY:
            self.__completes[view.path[1:]]=complete

        dep_count = int(trigger is not TRUE_DEPENDENCY) + \
                    int(time>timedelta.min)
        indent1=indent+1

        path='/'.join(view.path[1:])
        self.fd.write(f'{space*indent}<task name="{path}">\n')

        if 'RocotoResources' in view:
            for line in view.RocotoResources.splitlines():
                self.fd.write(f'{space*indent1}{line}\n')

        if dep_count==2:
            self.fd.write(space*indent1 + '<dependency> <and>\n')
        elif dep_count==1:
            self.fd.write(space*indent1 + '<dependency>\n')

        if trigger is not TRUE_DEPENDENCY:
            to_rocoto_dep(trigger,self.fd,indent1+1)
        if time>timedelta.min:
            to_rocoto_time_dep(time,self.fd,indent1+1)

        if dep_count==2:
            self.fd.write(space*indent1 + '</and> </dependency>\n')
        elif dep_count==1:
            self.fd.write(space*indent1 + '</dependency>\n')
        self.fd.write(space*indent+'</task>\n')

    def make_time_xml(self,indent=2):
        start_time=self.Clock.start.strftime('%Y%m%d%H%M')
        end_time=self.Clock.start.strftime('%Y%m%d%H%M')
        step=to_timedelta(self.Clock.step) # convert to python timedelta
        step=cycle_offset(step) # convert to rocoto time delta
        space=self.__spacing
        return f'{space*indent}<cycledef>{start_time} {end_time} {step}</cycledef>'

    def make_task_xml(self,indent=2):
        self.convert_family(indent,self.suite,TRUE_DEPENDENCY,FALSE_DEPENDENCY,
                            timedelta.min)
        self.handle_final_task(indent)

    def completes_for(self,item,with_completes):
        path=SuitePath(item.path[1:])

        if item.is_task():
            return item.is_complete() | self.__completes[item]

        # Initial completion dependency is the task or family
        # completion unless this item is the Suite.  Suites must be
        # handled differently.
        dep = item.is_complete() if path else FALSE_DEPENDENCY

        if path and path not in with_completes:
            # Families with no "complete" dependency in their entire
            # tree have no further dependencies to identify.  Their
            # own completion is the entirety of the completion
            # dependency.
            return dep

        for subitem in item.child_iter():
            if not isinstance(subitem,Taskable): continue
            dep=dep | self.completes_for(subitem,with_completes)

    def handle_final_task(self,indent):
        # Find and validate the "final" task:
        final=None
        if 'final' in self.suite:
            final=self.suite.final
            if not final.is_task():
                raise RocotoConfigError(
                    'For a workflow suite to be expressed in Rocoto, it '
                    'must have a "final" task with no dependencies')
            for elem in [ 'Trigger', 'Complete', 'Time', 'Perform' ]:
                if elem in final:
                    raise RocotoConfigError(
                      f'{elem}: In a Rocoto workflow, the "final" task '
                      'must have no dependencies and no performed actions.')

        if self.__completes and final is None:
            raise RocotoConfigError(
                'If a workflow suite has any "complete" conditions, '
                'then it must have a "final" task with no dependencies.')

        # Find all families that have tasks with completes:
        families_with_completes=set()
        for task in self.__completes:
            families_with_completes.add(task.path[1:-1])

        # Generate dependency for the final task:
        dep=self.completes_for(self.suite,families_with_completes)

    
def to_rocoto(suite,fd):
    tr=ToRocoto(suite,fd)
    tr.validate_cycle()
    tr.make_task_xml()

def test():
    from io import StringIO
    def to_string(action):
        sio=StringIO()
        action(sio)
        v=sio.getvalue()
        sio.close()
        return v
    dt=timedelta(seconds=7380,days=2)
    assert(cycle_offset(dt)=='50:03:00')
    assert(xml_quote('&<"')=='&amp;&lt;&quot;')
    then=datetime.strptime('2017-08-15','%Y-%m-%d')
    assert(to_rocoto_time(then+dt)=='201708170203')
    result=to_string(lambda x: to_rocoto_time_dep(dt,x,1))
    assert(result=='  <timedep>50:03:00</timedep>\n')
