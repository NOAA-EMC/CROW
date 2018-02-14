import sys, io
from datetime import timedelta, datetime
from io import StringIO
from copy import copy
from xml.sax.saxutils import quoteattr, escape

from crow.tools import typecheck
from collections import namedtuple
from collections.abc import Sequence, Mapping
from crow.tools import to_timedelta
import crow.sysenv
from crow.config import SuiteView, Suite, Depend, LogicalDependency, \
          AndDependency, OrDependency, NotDependency, \
          StateDependency, Dependable, Taskable, Task, \
          Family, Cycle, RUNNING, COMPLETED, FAILED, invalidate_cache, \
          TRUE_DEPENDENCY, FALSE_DEPENDENCY, SuitePath, TaskExistsDependency, \
          CycleExistsDependency, DataEvent, ShellEvent, EventDependency
from crow.metascheduler.algebra import simplify

__all__=['to_rocoto','RocotoConfigError','ToRocoto',
         'SelfReferentialDependency' ]

class RocotoConfigError(Exception): pass
class SelfReferentialDependency(RocotoConfigError): pass

_KEY_WARNINGS={ 'cyclethrottle':'Did you mean cycle_throttle?' }

_REQUIRED_KEYS={ 'workflow_install':'directory to receive Rocoto workflow',
                'scheduler':'Scheduler class',
                'workflow_xml': 'Contents of Rocoto XML file'}

_ROCOTO_STATE_MAP={ COMPLETED:'SUCCEEDED',
                   FAILED:'DEAD',
                   RUNNING:'RUNNING' }

_ROCOTO_DEP_TAG={ AndDependency:'and',
                 OrDependency:'or',
                 NotDependency:'not' }

_ZERO_DT=timedelta()

def stringify_clock(name,clock,indent):
    start_time=clock.start.strftime('%Y%m%d%H%M')
    end_time=clock.end.strftime('%Y%m%d%H%M')
    step=to_timedelta(clock.step) # convert to python timedelta
    step=_cycle_offset(step) # convert to rocoto time delta
    if name:
        return (f'{indent}<cycledef group="{name}">{start_time} '
                f'{end_time} {step}</cycledef>\n')
    else:
        return (f'{indent}<cycledef>{start_time} {end_time} '
                f'{step}</cycledef>\n')

def _dep_rel(dt,tree):
    tree.add_time(dt)
    return tree    

def _cycle_offset(dt):
    sign=''
    if dt<_ZERO_DT:
        dt=-dt
        sign='-'
    total=round(dt.total_seconds())
    hours=int(total//3600)
    minutes=int((total-hours*3600)//60)
    seconds=int(total-hours*3600-minutes*60)
    return f'{sign}{hours:02d}:{minutes:02d}:{seconds:02d}'


def _to_rocoto_dep_impl(dep,fd,indent):
    if type(dep) in _ROCOTO_DEP_TAG:
        tag=_ROCOTO_DEP_TAG[type(dep)]
        fd.write(f'{"  "*indent}<{tag}>\n')
        for d in dep: _to_rocoto_dep_impl(d,fd,indent+1)
        fd.write(f'{"  "*indent}</{tag}>\n')
    elif isinstance(dep,TaskExistsDependency):
        fd.write(f'{"  "*indent}<true></true> <!-- WARNING: ignoring "task exists" dependency on {".".join(dep.path[1:])}-->\n')
    elif isinstance(dep,StateDependency):
        path='.'.join(dep.path[1:])
        more=''
        if dep.path[0]!=_ZERO_DT:
            more=f' cycle_offset="{_cycle_offset(dep.path[0])}"'
        tag='taskdep' if dep.is_task() else 'metataskdep'
        attr='task' if dep.is_task() else 'metatask'
        if dep.state is COMPLETED:
            fd.write(f'{"  "*indent}<{tag} {attr}="{path}"{more}/>\n')
        else:
            state=_ROCOTO_STATE_MAP[dep.state]
            fd.write(f'{"  "*indent}<{tag} {attr}="{path}" state="{state}"/>\n')
    elif isinstance(dep,CycleExistsDependency):
        dt=_cycle_offset(dep.dt)
        fd.write(f'{"  "*indent}<cycleexistdep cycle_offset="{dt}"/>\n')
    elif isinstance(dep,EventDependency):
        event=dep.event
        if event.is_shell_event():
            if not 'command' in event:
                fd.write(f'{"  "*indent}<true></true><!-- shell dependency with no file -->\n')
            else:
                fd.write(f'{"  "*indent}<sh>{event.command}</sh>\n')
        elif event.is_data_event():
            if not 'file' in event:
                fd.write(f'{"  "*indent}<true></true><!-- data dependency with no file -->\n')
                return
            fd.write(f'{"  "*indent}<true></true><datadep')
            if 'age' in event:
                dt=crow.tools.str_timedelta(event.age).sub('d',':')
                fd.write(f' age={dt}')
            if 'minsize' in dep:
                nbytes=crow.tools.in_bytes(event.size)
                fd.write(f' size={nbytes}')
            fd.write(f'>{event.file}</datadep>\n')
        else:
            raise TypeError(f'Unexpected {type(event).__name__} event type in an EventDependency in _to_rocoto_dep')
    else:
        raise TypeError(f'Unexpected {type(dep).__name__} in _to_rocoto_dep')

def _to_rocoto_time_dep(dt,fd,indent):
    string_dt=_cycle_offset(dt)
    fd.write(f'{"  "*indent}<timedep>{string_dt}</timedep>\n')

def _to_rocoto_time(t):
    return t.strftime('%Y%m%d%H%M')

def _xml_quote(s):
    return s.replace('&','&amp;') \
            .replace('"','&quot;') \
            .replace('<','&lt;')

class ToRocoto(object):
    def __init__(self,suite):
        if not isinstance(suite,Suite):
            raise TypeError('The suite argument must be a Suite, '
                            'not a '+type(suite).__name__)

        try:
            settings=suite.Rocoto.scheduler
            scheduler=suite.Rocoto.scheduler
        except(AttributeError,IndexError,TypeError,ValueError) as e:
            raise ValueError('A Suite must define a Rocoto section containing '
                             'a "parallelism" and a "scheduler."')

        update_globals={ 'sched':scheduler, 'to_rocoto':self,
                         'metasched':self }
        if 'parallelism' in suite.Rocoto:
            update_globals['parallelism']=suite.Rocoto.parallelism

        self.type='rocoto'
        self.suite=suite
        self.suite.update_globals(**update_globals)
        self.settings=self.suite.Rocoto
        self.sched=scheduler
        self.__all_defined=set()
        self.__completes=dict()
        self.__families=set()
        self.__spacing=suite.Rocoto.get('indent_text','  ')
        self.__rocotoified=dict()
        if not isinstance(self.__spacing,str):
            raise TypeError("Suite's Rocoto.indent_text, if present, "
                            "must be a string.")
        self.__dummy_var_count=0
        self.__families_with_completes=set()
        self.__alarms_used=set([""])

    def defenvar(self,name,value):
        return f'<envar><name>{name}</name><value>{value!s}</value></envar>'

    def defvar(self,name,value):
        qvalue=quoteattr(str(value))
        return(f'<!ENTITY {name} {qvalue}>')

    def varref(self,name):
        return f'&{name};'

    def make_time_xml(self,indent=1):
        with io.StringIO() as sio:
            for name in self.__alarms_used:
                if name:
                    alarm=self.suite.Alarms[name]
                else:
                    alarm=self.suite.Clock
                sio.write(stringify_clock(name,alarm,indent*self.__spacing))
            return sio.getvalue()

    def make_task_xml(self,indent=1):
        fd=StringIO()
        self._record_item(self.suite,FALSE_DEPENDENCY)

        # Find all families that have tasks with completes:
        for path,view_condition in self.__completes.items():
            (view,condition) = view_condition
            for i in range(1,len(path)):
                family_path=SuitePath(path[1:i])
                self.__families_with_completes.add(family_path)

        self._convert_item(fd,max(0,indent-1),self.suite,TRUE_DEPENDENCY,
                           FALSE_DEPENDENCY,timedelta.min,'')
        self._handle_final_task(fd,indent)
        result=fd.getvalue()
        fd.close()
        return result

    # ----------------------------------------------------------------

    # Protected member functions

    def _has_completes(self,item):
        for i in range(2,len(item)):
            path=SuitePath([_ZERO_DT] + item.path[1:i])
            if path in self.__completes:
                return True
        return False

    def _rocotoify_dep(self,dep,defining_path):
        try:
            if dep in self.__rocotoified:
                return self.__rocotoified[dep]
            roco=self._rocotoify_dep_impl(dep,defining_path)
            self.__rocotoified[dep]=roco
            return roco
        except RecursionError as re:
            raise SelfReferentialDependency(
                f'/{"/".join([str(d) for d in defining_path[1:]])}: '
                'cyclic dependency graph referenced from this task.')

    def _rocotoify_dep_impl(self,dep,defining_path):
        if isinstance(dep,StateDependency):
            dep_path=SuitePath([_ZERO_DT] + dep.view.path[1:])
            if dep_path not in self.__all_defined:
                raise ValueError(
                    f'/{"/".join(defining_path[1:])}: '
                    'has a dependency on undefined task '
                    f'/{"/".join(dep_path[1:])}')


        if isinstance(dep,StateDependency) and not dep.view.is_task() and \
           dep.state==RUNNING:
            deplist=list()
            for t in dep.view.walk_task_tree():
                if t.is_task():
                    deplist.append(t.is_running())
            if not deplist: return FALSE_DEPENDENCY # no tasks
            return _dep_rel(dep.view.path[0],OrDependency(*deplist))
        elif isinstance(dep,StateDependency) and dep.state==COMPLETED:
            zero_path=SuitePath([_ZERO_DT]+dep.view.path[1:])
            if dep.view.is_task():
                if zero_path in self.__completes:
                    return dep | _dep_rel(dep.view.path[0],self._rocotoify_dep(
                        self._completes_for(dep.view),defining_path))
            elif SuitePath(dep.view.path[1:]) in self.__families_with_completes:
                deplist=list()
                for t in dep.view.walk_task_tree():
                    if t.is_task():
                        deplist.append(_dep_rel(dep.view.path[0],self._rocotoify_dep(
                            t.is_completed(),defining_path)))
                return AndDependency(*deplist)  | _dep_rel(dep.path[0], \
                      self._rocotoify_dep(self._completes_for(dep.view),
                                          defining_path))
        elif isinstance(dep,NotDependency):
            return NotDependency(self._rocotoify_dep(dep.depend,defining_path))
        elif isinstance(dep,OrDependency) or isinstance(dep,AndDependency):
            cls=type(dep)
            for i in range(len(dep.depends)):
                dep.depends[i]=self._rocotoify_dep(dep.depends[i],defining_path)
        return dep

    def _as_rocoto_dep(self,dep,defining_path):
        dep=dep.copy_dependencies()
        dep=self._rocotoify_dep(dep,defining_path)
        dep=simplify(dep)
        return dep

    def _expand_workflow_xml(self):
        return self.settings.workflow_xml

    def _validate_cycle(self):
        """!Perform sanity checks on top level of suite."""
        settings=self.settings
        for key,what in _REQUIRED_KEYS.items():
            if key not in settings:
                raise KeyError('%s: missing variable (%s)'%(key,what))

        for key,what in _KEY_WARNINGS.items():
            if key in settings:
                raise KeyError('%s: %s'%(key,what))

    def _record_item(self,view,complete):
        if view.get('Disable',False):          return
        complete=complete | view.get_complete_dep()
        self.__all_defined.add(view.path)

        if complete is not FALSE_DEPENDENCY:
            complete=complete | view.get_complete_dep()
            self.__completes[view.path]=[view, complete]

        if view.is_task():
            return

        self.__families.add(SuitePath(view.path[1:-1]))

        for key,child in view.items():
            if key in [ 'up', 'this' ]: continue
            if not isinstance(child,SuiteView):
                continue
            if child.path[1:] == ['final']:
                if not child.is_task():
                    raise RocotoConfigError(
                        'The "final" task must be a Task, not a '
                        +type(child.viewed).__name__)
                self.__final_task=child
            else:
                self._record_item(child,complete)

    def _convert_item(self,fd,indent,view,trigger,complete,time,alarm_name):
        if view.get('Disable',False):          return
        trigger=trigger & view.get_trigger_dep()
        complete=complete | view.get_complete_dep()
        time=max(time,view.get_time_dep())
        space=self.__spacing

        if 'AlarmName' in view:
            if alarm_name:
                raise ValueError('{view.task_path_var}: nested alarms are not supported in crow.metascheduler.to_rocoto()')
            else:
                alarm_name=view.AlarmName

        if view.is_task():
            maxtries=int(view.get(
                'max_tries',self.suite.Rocoto.get('max_tries',0)))
            attr = f' maxtries="{maxtries}"' if maxtries else ''
            self._write_task_text(fd,attr,indent,view,trigger&~complete,time,alarm_name)
            return

        self.__dummy_var_count+=1
        dummy_var="dummy_var_"+str(self.__dummy_var_count)

        path=_xml_quote('.'.join(view.path[1:]))
        if not isinstance(view,Suite):
            fd.write(f'''{space*indent}<metatask name="{path}">
{space*indent}  <var name="{dummy_var}">DUMMY_VALUE</var>
''')
        for key,child in view.items():
            if key in [ 'up', 'this' ]: continue
            if not isinstance(child,SuiteView):
                continue
            if child.path[1:] == ['final']:
                if not child.is_task():
                    raise RocotoConfigError(
                        'The "final" task must be a Task, not a '
                        +type(child.viewed).__name__)
                self.__final_task=child
            else:
                self._convert_item(fd,indent+1,child,trigger,complete,time,alarm_name)

        if not isinstance(view,Suite):
            fd.write(f'{space*indent}</metatask>\n')

    def _write_task_text(self,fd,attr,indent,view,dependency,time,alarm_name,
                         manual_dependency=None):
        path='.'.join(view.path[1:])
        space=self.__spacing
        fd.write(f'{space*indent}<task name="{path}"{attr}')
        if alarm_name:
            self.__alarms_used.add(alarm_name)
            fd.write(f' cycledefs="{alarm_name}"')
        fd.write('>\n')

        dep=self._as_rocoto_dep(dependency,view.path)

        dep_count = ( dep != TRUE_DEPENDENCY ) + ( time>timedelta.min )

        if 'Rocoto' in view:
            for line in view.Rocoto.splitlines():
                fd.write(f'{space*(indent+1)}{line}\n')

        if manual_dependency is not None:
            for line in manual_dependency.splitlines():
                fd.write(f'{space*(indent+1)}{line}\n')
            fd.write(space*indent+'</task>\n')
            return

        if not dep_count:
            fd.write(space*(indent+1) + '<!-- no dependencies -->\n')
        if dep_count:
            fd.write(space*(indent+1) + '<dependency>\n')
        if dep_count>1:
            fd.write(space*(indent+2) + '<and>\n')

        if dep is not TRUE_DEPENDENCY:
            _to_rocoto_dep_impl(dep,fd,indent+1+dep_count)
        if time>timedelta.min:
            _to_rocoto_time_dep(time,fd,indent+1+dep_count)

        if dep_count>1:
            fd.write(space*(indent+2) + '</and>\n')
        if dep_count:
            fd.write(space*(indent+1) + '</dependency>\n')
        fd.write(space*indent+'</task>\n')

    def _completes_for(self,item):
        dep=FALSE_DEPENDENCY
        for i in range(1,len(item.path)):
            item_path=SuitePath(item.path[0:i+1])
            if item_path in self.__completes:
                dep=dep | self.__completes[item_path][1]
        return dep

    def _final_task_deps(self,item,for_alarm=None,alarm_name=None):
        path=SuitePath(item.path[1:])
        with_completes=self.__families_with_completes

        if for_alarm is not None:
            if 'AlarmName' in item:
                if alarm_name:
                    raise ValueError('{item.task_path_var}: nested alarms are not supported in crow.metascheduler.to_rocoto()')
                else:
                    alarm_name=item.AlarmName
            if alarm_name is not None and alarm_name != for_alarm:
                return TRUE_DEPENDENCY

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
            subdep=subdep & self._final_task_deps(subitem,for_alarm,alarm_name)

        if dep is FALSE_DEPENDENCY:
            dep=subdep
        else:
            dep=dep | subdep

        return dep

    def _handle_final_task(self,fd,indent):
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

        if len(self.__alarms_used)<2:
            # There are no alarms in use, so there is only one final task.
            # Generate dependency for it:
            fd.write(f'\n{self.__spacing*indent}<!-- The final task dependencies are automatically generated to handle Complate and Trigger conditions. -->\n\n')
            dep=self._final_task_deps(self.suite)
            self._write_task_text(fd,' final="true"',indent,final,dep,timedelta.min,'')
            return
            

        fd.write(f'\n{self.__spacing*indent}<!-- These final tasks are automatically generated to handle Complate and Trigger conditions, and alarms. -->\n\n')

        # There are alarms, so things get... complicated.
        manual_dependency=f'''<dependency>
{self.__spacing*indent}<and>
{self.__spacing*(indent+1)}<!-- All tasks must be complete or invalid for this cycle -->\n'''
        for alarm_name in self.__alarms_used:
            this_alarm_final_dep=self._final_task_deps(self.suite,for_alarm=alarm_name)
            task_name=f'final_for_{alarm_name}' if alarm_name else 'final_no_alarm'
            new_task=copy(self.suite.final.viewed)
            new_task['AlarmName']=alarm_name
            invalidate_cache(new_task)
            self.suite.viewed[task_name]=new_task
            new_task_view=self.suite[task_name]
            del new_task
            self.__all_defined.add(SuitePath(
                [_ZERO_DT] + new_task_view.path[1:]))
            self._write_task_text(fd,' final="true"',indent,new_task_view,
                                  this_alarm_final_dep,timedelta.min,alarm_name)
            
            manual_dependency+=f'''{self.__spacing*(indent+1)}<or>
{self.__spacing*(indent+2)}<taskdep task="{task_name}"/>
{self.__spacing*(indent+2)}<not><taskvalid task="{task_name}"/></not>
{self.__spacing*(indent+1)}</or>\n'''
        manual_dependency+=f'{self.__spacing*indent}</and>\n</dependency>\n'
        self._write_task_text(
            fd,' final="true"',indent,final,
            TRUE_DEPENDENCY,timedelta.min,'',
            manual_dependency=manual_dependency)
def to_rocoto(suite):
    typecheck('suite',suite,Suite)
    return ToRocoto(suite)._expand_workflow_xml()

def test():
    def to_string(action):
        sio=StringIO()
        action(sio)
        v=sio.getvalue()
        sio.close()
        return v
    dt=timedelta(seconds=7380,days=2)
    assert(_cycle_offset(dt)=='50:03:00')
    assert(_xml_quote('&<"')=='&amp;&lt;&quot;')
    then=datetime.strptime('2017-08-15','%Y-%m-%d')
    assert(_to_rocoto_time(then+dt)=='201708170203')
    result=to_string(lambda x: _to_rocoto_time_dep(dt,x,1))
    assert(result=='  <timedep>50:03:00</timedep>\n')
