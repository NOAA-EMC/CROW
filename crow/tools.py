import subprocess
import os, re
from collections.abc import MutableMapping

__all__=['panasas_gb','gpfs_gb']

def panasas_gb(dir):
    rdir=os.path.realpath(dir)
    stdout=subprocess.check_output(['pan_df','-B','1G','-P',rdir])
    for line in stdout.splitlines():
        if rdir in str(line):
            return int(line.split()[3],10)
    return 0
#pan_df -B 1G -P /scratch4/NCEPDEV/stmp3/
#Filesystem         1073741824-blocks      Used Available Capacity Mounted on
#panfs://10.181.12.11/     94530     76432     18098      81% /scratch4/NCEPDEV/stmp3/

def gpfs_gb(dir,fileset,device):
    mmlsquota=subprocess.check_output([
        'mmlsquota', '--block-size', '1T'])
    for m in re.finditer(b'''(?isx)
               (?:
                   \S+ \s+ FILESET
                   \s+ (?P<TBused>  \d+  )
                   \s+ (?P<TBquota> \d+  )
                   \s+ (?P<TBlimit> \d+  )
                   [^\r\n]* (?: [\r\n] | [\r\n]*\Z )
                |
                 (?P<bad> [^\r\n]*[\r\n] | [^\r\n]*\Z )
               )
               ''',mmlsquota):
        
        if m.group('bad') or not m.group('TBused') \
           or not m.group('TBlimit'):
            continue
        return 1024*(int(m.group('TBlimit')) - int(m.group('TBused')))
    return 0
    
class ImmutableMapping(MutableMapping):
    """Immutable dictionary"""

    def __init__(self,*args,**kwargs): self.__dict=dict(*args,**kwargs)
    def __len__(self):                 return len(self.__dict)
    def __getitem__(self,k):           return self.__dict[k]
    def __getattr__(self,name):        return self[name]
    def __iter__(self):
        for i in self.__dict:
            yield i
    def __setitem__(self,k,v): raise Exception('Immutable object')
    def __delitem__(self,k):   raise Exception('Immutable object')


