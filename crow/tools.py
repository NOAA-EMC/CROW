import subprocess
import os, re
from datetime import timedelta
from copy import deepcopy
from collections.abc import Mapping

__all__=['panasas_gb','gpfs_gb','to_timedelta']

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
    
class ImmutableMapping(Mapping):
    """Immutable dictionary"""

    def __deepcopy__(self,memo):
        im=ImmutableMapping()
        im.__dict=dict([ (deepcopy(k),deepcopy(v)) \
                         for k,v in self.__dict.items() ])
        return im
    def __init__(self,*args,**kwargs): self.__dict=dict(*args,**kwargs)
    def __len__(self):                 return len(self.__dict)
    def __getitem__(self,k):           return self.__dict[k]
    def __getattr__(self,name):        return self[name]
    def __iter__(self):
        for i in self.__dict:
            yield i



########################################################################

DT_REGEX={
    u'(\d+):(\d+)':(
        lambda m: timedelta(hours=m[0],minutes=m[1]) ),
    u'(\d+):(\d+):(\d+)':(
        lambda m: timedelta(hours=m[0],minutes=m[1],seconds=m[2]) ),
    u'(\d+)d(\d+)h':(
        lambda m: timedelta(days=m[0],hours=m[1])),
    u'(\d+)d(\d+):(\d+)':(
        lambda m: timedelta(days=m[0],hours=m[1],minutes=m[2])),
    u'(\d+)d(\d+):(\d+):(\d+)':(
        lambda m: timedelta(days=m[0],hours=m[1],minutes=m[2],
                            seconds=m[3]))
    }

def to_timedelta(s):
    if isinstance(s,timedelta): return s
    if not isinstance(s,str):
        raise TypeError('Argument to to_timedelta must be a str not a %s'%(
            type(s).__name__,))
    mult=1
    if s[0]=='-':
        s=s[1:]
        mult=-1
    elif s[0]=='+':
        s=s[1:]
    for regex,fun in DT_REGEX.items():
        m=re.match(regex,s)
        if m:
            ints=[ int(s,10) for s in m.groups() ]
            return mult*fun(ints)
    raise ValueError(s+': invalid timedelta specification (12:34, '
                     '12:34:56, 9d12h, 9d12:34, 9d12:34:56)')

########################################################################

def to_printf_octal(match):
    """!Intended to be sent to re.sub to replace a single byte match with
    a printf-style octal representation of that byte"""
    i=int.from_bytes(match[1],'big',signed=False)
    return b'\\%03o'%i

def str_to_posix_sh(s,encoding='ascii'):
    """!Convert a string to a POSIX sh represesntation of that string.
    Will produce undefined results if the string is not a valid ASCII
    string.    """

    # Convert from unicode to ASCII:
    if not isinstance(s,bytes):
        if not isinstance(s,str):
            raise TypeError('str_to_posix_sh: argument must be a str '
                            f'or bytes, not a {type(s).__name__}')
        s=bytes(s,'ascii')

    # For strins with no special characterrs, return unmodified
    if re.match(br'(?ms)[a-zA-Z0-9_+:/.,-]+$',s):
        return s

    # For characters that have a special meaning in sh "" strings,
    # prepend a backslash (\):
    s=re.sub(br'(?ms)(["\\])',br'\\\1',s)

    if re.search(br'(?ms)[^ -~]',s):
        # String contains special characters.  Use printf.
        s=re.sub(b'(?ms)([^ -~])',to_printf_octal,s)
        return b'"$( printf \'' + s + b'\' )"'

    return b'"'+s+b'"'
