import crow.tools
import os.path
import os
import datetime
from crow.config.exceptions import *

class Environment(dict):
    def __getattr__(self,key):
        if key in self: return self[key]
        raise AttributeError(key)

ENV=Environment(os.environ)

def strftime(d,fmt): return d.strftime(fmt)
def YMDH(d): return d.strftime('%Y%m%d%H')
def YMD(d): return d.strftime('%Y%m%d')

## The CONFIG_TOOLS contains the tools available to configuration yaml
## "!calc" expressions in their "tools" variable.
CONFIG_TOOLS=crow.tools.ImmutableMapping({
    'panasas_gb':crow.tools.panasas_gb,
    'gpfs_gb':crow.tools.gpfs_gb,
    'basename':os.path.basename,
    'dirname':os.path.dirname,
    'abspath':os.path.abspath,
    'realpath':os.path.realpath,
    'isdir':os.path.isdir,
    'isfile':os.path.isfile,
    'islink':os.path.islink,
    'exists':os.path.exists,
    'strftime':strftime,
    'YMDH':YMDH,
    'YMD':YMD,
})
