import crow.tools
import os.path
import os
import datetime
from collections import Sequence, Mapping
from crow.config.exceptions import *
import crow.sysenv

class Environment(dict):
    def __getattr__(self,key):
        if key in self: return self[key]
        raise AttributeError(key)

ENV=Environment(os.environ)

def strftime(d,fmt): return d.strftime(fmt)
def strptime(d,fmt): return datetime.datetime.strptime(d,fmt)
def to_YMDH(d): return d.strftime('%Y%m%d%H')
def to_YMD(d): return d.strftime('%Y%m%d')
def from_YMDH(d): return datetime.datetime.strptime(d,'%Y%m%d%H')
def from_YMD(d): return datetime.datetime.strptime(d,'%Y%m%d')
def join(L,J): return J.join(L)
def seq(start,end,step):
    return [ r for r in range(start,end+1,step) ]

def fort(value,scope='scope'):
    """!Convenience function to convert a python object to a syntax valid
    in fortran namelists.    """
    if isinstance(value,str):
        return repr(value)
    elif isinstance(value,Sequence):
        # For sequences, convert to a namelist list.
        result=[]
        for item in value:
            assert(item is not value)
            fortitem=fort(item,scope)
            result.append(fortitem)
        return ", ".join(result)
    elif isinstance(value,Mapping):
        # For mappings, assume a derived type.
        subscope_keys=[ (f'{scope}%{key}',value) for key in value ]
        return ', '.join([f'{k}={fort(v,k)}' for (k,v) in subscope_keys])
    elif value is True or value is False:
        # Booleans get a "." around them:
        return '.'+str(bool(value))+'.'
    elif isinstance(value,float):
        return '%.12g'%value
    else:
        # Anything else is converted to a string.
        return str(value)

def seconds(dt):
    if not isinstance(dt,datetime.timedelta):
        raise TypeError(f'dt must be a timedelta not a {type(dt).__name__}')
    return dt.total_seconds()

def crow_install_dir(rel=None):
    path=os.path.dirname(__file__)
    path=os.path.join(path,'../..')
    if rel:
        path=os.path.join(path,rel)
    return os.path.abspath(path)

MISSING=object()
def env(var,default=MISSING):
    if default is MISSING:
        return os.environ[var]
    return os.environ.get(var,default)

def have_env(var): return var in os.environ

## The CONFIG_TOOLS contains the tools available to configuration yaml
## "!calc" expressions in their "tools" variable.
CONFIG_TOOLS=crow.tools.ImmutableMapping({
    'fort':fort,
    'seq':seq,
    'crow_install_dir':crow_install_dir,
    'panasas_gb':crow.tools.panasas_gb,
    'gpfs_gb':crow.tools.gpfs_gb,
    'basename':os.path.basename,
    'dirname':os.path.dirname,
    'abspath':os.path.abspath,
    'realpath':os.path.realpath,
    'isdir':os.path.isdir,
    'isfile':os.path.isfile,
    'env':env,
    'have_env':have_env,
    'islink':os.path.islink,
    'exists':os.path.exists,
    'strftime':strftime,
    'strptime':strptime,
    'to_timedelta':crow.tools.to_timedelta,
    'as_seconds':seconds,
    'to_YMDH':to_YMDH, 'from_YMDH':from_YMDH,
    'to_YMD':to_YMD, 'from_YMD':from_YMD,
    'join':join,
    'get_parallelism':crow.sysenv.get_parallelism, 
    'get_scheduler':crow.sysenv.get_scheduler,
    'node_tool_for':crow.sysenv.node_tool_for,
})
