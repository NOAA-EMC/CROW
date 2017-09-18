import sys
from datetime import timedelta, datetime
from io import StringIO
from collections import namedtuple
from collections.abc import Sequence, Mapping
from crow.tools import to_timedelta
import crow.sysenv
from crow.config import SuiteView, Suite, Depend, LogicalDependency, \
          AndDependency, OrDependency, NotDependency, \
          StateDependency, Dependable, Taskable, Task, \
          Family, Cycle, RUNNING, COMPLETED, FAILED, \
          TRUE_DEPENDENCY, FALSE_DEPENDENCY, SuitePath, \
          CycleExistsDependency
from crow.metascheduler.simplify import simplify

__all__=['ToRocoto','RocotoConfigError']

KEY_WARNINGS={ 'cyclethrottle':'Did you mean cycle_throttle?' }

MISSING=object()

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
    sign=''
    if dt<ZERO_DT:
        dt=-dt
        sign='-'
    total=round(dt.total_seconds())
    hours=int(total//3600)
    minutes=int((total-hours*3600)//60)
    seconds=int(total-hours*3600-minutes*60)
    return f'{sign}{hours:02d}:{minutes:02d}:{seconds:02d}'

def to_rocoto_dep(dep,fd,indent):
    dep=simplify(dep)
    if type(dep) in ROCOTO_DEP_TAG:
        tag=ROCOTO_DEP_TAG[type(dep)]
        fd.write(f'{"  "*indent}<{tag}>\n')
        for d in dep: to_rocoto_dep(d,fd,indent+1)
        fd.write(f'{"  "*indent}</{tag}>\n')
    elif isinstance(dep,StateDependency):
        path='.'.join(dep.path[1:])
        more=''
        if dep.path[0]!=ZERO_DT:
            more=f' cycle_offset="{cycle_offset(dep.path[0])}"'
        tag='taskdep' if dep.is_task() else 'metataskdep'
        attr='task' if dep.is_task() else 'metatask'
        if dep.state is COMPLETED:
            fd.write(f'{"  "*indent}<{tag} {attr}="{path}"{more}/>\n')
        else:
            state=ROCOTO_STATE_MAP[dep.state]
            fd.write(f'{"  "*indent}<{tag} {attr}="{path}" state="{state}"/>\n')
    elif isinstance(dep,CycleExistsDependency):
        dt=cycle_offset(dep.dt)
        fd.write(f'{"  "*indent}<cycleexistdep cycle_offset="{dt}"/>\n')
    else:
        raise TypeError(f'Unexpected {type(dep).__name__} in to_rocoto_dep')

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
    def __init__(self,suite):
        if not isinstance(suite,Cycle):
            raise TypeError('The suite argument must be a Cycle, '
                            'not a '+type(suite).__name__)

        try:
            settings=suite.Rocoto.scheduler
            scheduler_name=suite.Rocoto.scheduler.name
            parallelism=suite.Rocoto.parallelism
            parallelism_name=parallelism.name
            sched=crow.sysenv.get_scheduler(scheduler_name,settings)
            runner=crow.sysenv.get_parallelism(parallelism_name,settings)
        except(AttributeError,IndexError,TypeError,ValueError) as e:
            raise ValueError('A Suite must define a Rocoto section containing '
                             'the "parallelism" and "scheduler" settings.')

        self.suite=Suite(suite,{'sched':sched,'to_rocoto':self,
                                'runner':runner})
        self.settings=self.suite.Rocoto
        self.sched=sched
        self.__completes=dict()
        self.__families=set()
        self.__spacing=suite.Rocoto.get('indent_text','  ')
        if not isinstance(self.__spacing,str):
            raise TypeError("Suite's Rocoto.indent_text, if present, "
                            "must be a string.")
        self.__dummy_var_count=0

    def expand_workflow_xml(self):
        return self.settings.workflow_xml

    def validate_cycle(self):
        """!Perform sanity checks on top level of suite."""
        settings=self.settings
        for key,what in REQUIRED_KEYS.items():
            if key not in settings:
                raise KeyError('%s: missing variable (%s)'%(key,what))

        for key,what in KEY_WARNINGS.items():
            if key in settings:
                raise KeyError('%s: %s'%(key,what))

    def convert_family(self,fd,indent,view,trigger,complete,time):
        trigger=trigger & view.get_trigger_dep()
        complete=complete | view.get_complete_dep()
        time=max(time,view.get_time_dep())
        space=self.__spacing

        self.__dummy_var_count+=1
        dummy_var="dummy_var_"+str(self.__dummy_var_count)

        path=xml_quote('.'.join(view.path[1:]))
        if not isinstance(view,Suite):
            fd.write(f'''{space*indent}<metatask name="{path}">
{space*indent}  <var name="{dummy_var}">DUMMY_VALUE</var>
''')
        self.__families.add(SuitePath(view.path[1:-1]))

        for key,child in view.items():
            if key=='up': continue
            if not isinstance(child,SuiteView):
                continue
            if child.path[1:] == ['final']:
                if not child.is_task():
                    raise RocotoConfigError(
                        'The "final" task must be a Task, not a '
                        +type(child.viewed).__name__)
                self.__final_task=child
            elif child.is_task():
                self.convert_task(fd,indent+1,child,trigger,complete,time)
            else:
                self.convert_family(fd,indent+1,child,trigger,complete,time)

        if not isinstance(view,Suite):
            fd.write(f'{space*indent}</metatask>\n')

    def convert_task(self,fd,indent,view,trigger,complete,time):
        trigger=trigger & view.get_trigger_dep()
        complete=complete | view.get_complete_dep()
        time=max(time,view.get_time_dep())

        dep=trigger
        if complete is not FALSE_DEPENDENCY:
            self.__completes[view.path]=[view, complete]
            dep = dep & ~ complete

        dep_count = int(trigger is not TRUE_DEPENDENCY) + \
                    int(time>timedelta.min)
        maxtries=int(view.get('max_tries',self.suite.Rocoto.get('max_tries',0)))
        attr = f' maxtries="{maxtries}"' if maxtries else ''
        self.write_task_text(fd,attr,indent,view,dep_count,dep,time)

    def write_task_text(self,fd,attr,indent,view,dep_count,trigger,time):
        path='.'.join(view.path[1:])
        indent1=indent+1
        space=self.__spacing
        fd.write(f'{space*indent}<task name="{path}"{attr}>\n')

        if 'Rocoto' in view:
            for line in view.Rocoto.splitlines():
                fd.write(f'{space*indent1}{line}\n')

        if not dep_count:
            fd.write(space*indent1 + '<!-- no dependencies -->\n')
        if dep_count:
            fd.write(space*indent1 + '<dependency>\n')
        if dep_count>1:
            fd.write(space*indent1 + '<and>\n')

        if trigger is not TRUE_DEPENDENCY:
            to_rocoto_dep(trigger,fd,indent1+1)
        if time>timedelta.min:
            to_rocoto_time_dep(time,fd,indent1+1)

        if dep_count>1:
            fd.write(space*indent1 + '</and>\n')
        if dep_count:
            fd.write(space*indent1 + '</dependency>\n')
        fd.write(space*indent+'</task>\n')

    def make_time_xml(self,indent=1):
        clock=self.suite.Clock
        start_time=clock.start.strftime('%Y%m%d%H%M')
        end_time=clock.end.strftime('%Y%m%d%H%M')
        step=to_timedelta(clock.step) # convert to python timedelta
        step=cycle_offset(step) # convert to rocoto time delta
        space=self.__spacing
        return f'{space*indent}<cycledef>{start_time} {end_time} {step}</cycledef>\n'

    def make_task_xml(self,indent=1):
        fd=StringIO()
        self.convert_family(fd,max(0,indent-1),self.suite,TRUE_DEPENDENCY,
                            FALSE_DEPENDENCY,timedelta.min)
        self.handle_final_task(fd,indent)
        result=fd.getvalue()
        fd.close()
        return result

    def completes_for(self,fd,item,with_completes):
        path=SuitePath(item.path[1:])

        if item.is_task():
            dep = item.is_completed()
            if item.path in self.__completes:
                dep = dep | self.__completes[item.path][1]
            return dep

        # Initial completion dependency is the task or family
        # completion unless this item is the Suite.  Suites must be
        # handled differently.
        if path:
            dep = item.is_completed() # Family SuiteView
        else:
            dep = FALSE_DEPENDENCY   # Suite

        if path and path not in with_completes:
            # Families with no "complete" dependency in their entire
            # tree have no further dependencies to identify.  Their
            # own completion is the entirety of the completion
            # dependency.
            return dep

        subdep=TRUE_DEPENDENCY
        for subitem in item.child_iter():
            if not path and subitem.path[1:] == [ 'final' ]:
                # Special case.  Do not include final task's
                # dependency in the final task's dependency.
                continue
            if not isinstance(subitem,SuiteView):
                continue
            subdep=subdep & self.completes_for(fd,subitem,with_completes)

        if dep is FALSE_DEPENDENCY:
            dep=subdep
        else:
            dep=dep | subdep

        return dep

    def handle_final_task(self,fd,indent):
        # Find and validate the "final" task:
        final=None
        if 'final' in self.suite:
            final=self.suite.final
            if not final.is_task():
                raise RocotoConfigError(
                    'For a workflow suite to be expressed in Rocoto, it '
                    'must have a "final" task')
            for elem in [ 'Trigger', 'Complete', 'Time' ]:
                if elem in final:
                    raise RocotoConfigError(
                      f'{elem}: In a Rocoto workflow, the "final" task '
                      'must have no dependencies.')

        if self.__completes and final is None:
            raise RocotoConfigError(
                'If a workflow suite has any "complete" conditions, '
                'then it must have a "final" task with no dependencies.')

        # Find all families that have tasks with completes:
        families_with_completes=set()
        for path,view_condition in self.__completes.items():
            (view,condition) = view_condition
            for i in range(1,len(path)):
                family_path=SuitePath(path[1:i])
                families_with_completes.add(family_path)

        # Generate dependency for the final task:
        dep=self.completes_for(fd,self.suite,families_with_completes)

        self.write_task_text(fd,' final="true"',indent,final,1,dep,timedelta.min)
        
def to_rocoto(suite):
    assert(isinstance(suite,Cycle))
    tr=ToRocoto(suite)
    return tr.expand_workflow_xml()

def test():
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
