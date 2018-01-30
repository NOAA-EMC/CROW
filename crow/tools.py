import subprocess, os, re, logging, tempfile, datetime, shutil
from datetime import timedelta
from copy import deepcopy
from contextlib import suppress
from collections.abc import Mapping

__all__=['panasas_gb','gpfs_gb','to_timedelta','deliver_file']
_logger=logging.getLogger('crow.tools')

def deliver_file(from_file: str,to_file: str,*,blocksize: int=1048576,
                 permmask: int=2,preserve_perms: bool=True,
                 preserve_times: bool=True,preserve_group: bool=True,
                 mkdir: bool=True) -> None:
    to_dir=os.path.dirname(to_file)
    to_base=os.path.basename(to_file)
    if mkdir and to_dir and not os.path.isdir(to_dir):
        _logger.info(f'{to_dir}: makedirs')
        os.makedirs(to_dir)
    temppath=None # type: str
    _logger.info(f'{to_file}: deliver from {from_file}')
    try:
        with open(from_file,'rb') as in_fd:
            istat=os.fstat(in_fd.fileno())
            with tempfile.NamedTemporaryFile(
                    prefix=f"_tmp_{to_base}.part.",
                    delete=False,dir=to_dir) as out_fd:
                temppath=out_fd.name
                shutil.copyfileobj(in_fd,out_fd,length=blocksize)
        assert(temppath)
        assert(os.path.exists(temppath))
        if preserve_perms:
            os.chmod(temppath,istat.st_mode&~permmask)
        if preserve_times:
            os.utime(temppath,(istat.st_atime,istat.st_mtime))
        if preserve_group:
            os.chown(temppath,-1,istat.st_gid)
        os.rename(temppath,to_file)
        temppath=None
    except Exception as e:
        _logger.warning(f'{to_file}: {e}')
        raise
    finally: # Delete file on error
        if temppath and os.path.exists(temppath): os.unlink(temppath)

def panasas_gb(dir,pan_df='pan_df'):
    rdir=os.path.realpath(dir)
    stdout=subprocess.check_output([pan_df,'-B','1G','-P',rdir])
    for line in stdout.splitlines():
        if rdir in str(line):
            return int(line.split()[3],10)
    return 0
#pan_df -B 1G -P /scratch4/NCEPDEV/stmp3/
#Filesystem         1073741824-blocks      Used Available Capacity Mounted on
#panfs://10.181.12.11/     94530     76432     18098      81% /scratch4/NCEPDEV/stmp3/

def gpfs_gb(dir,fileset,device,mmlsquota='mmlsquota'):
    mmlsquota=subprocess.check_output([
        mmlsquota, '--block-size', '1T'])
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
    if isinstance(s,int): return timedelta(seconds=s)
    if isinstance(s,float): return timedelta(seconds=round(s))
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

def memory_in_bytes(s):
    """!Converts 1kb, 3G, 9m, etc. to a number of bytes.  Understands
    k, M, G, P, E (caseless) with optional "b" suffix.  Uses powers of
    1024 for scaling (kibibytes, mibibytes, etc.)"""
    scale = { 'k':1, 'K':1, 'm':2, 'M':2, 'g':3, 'G':3,
              'p':4, 'P':4, 'e':5, 'E':5 }
    if s[-1]=='b': s=s[:-1]
    multiplier=1
    if s[-1] in scale:
        multiplier=1024**scale[s[-1]]
        s=s[:-1]
    return float(s)*multiplier

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

def typecheck(name,obj,cls,tname=None):
    if not isinstance(obj,cls):
        if tname is None: tname=cls.__name__
        msg=f'{name!s} must be type {tname} not {type(obj).__name__!s}'
        raise TypeError(msg)

########################################################################

ZERO_DT=timedelta()
class Clock(object):
    def __init__(self,start,step,end=None,now=None):
        typecheck('start',start,datetime.datetime)
        typecheck('step',step,datetime.timedelta)
        if end is not None:
            typecheck('end',end,datetime.datetime)
        self.start=start
        self.end=end
        self.step=step
        self.__now=start
        if self.step<=ZERO_DT:
            raise ValueError('Time step must be positive and non-zero.')
        if self.end<self.start:
            raise ValueError('End time must be at or after start time.')
        self.now=now

    def __contains__(self,when):
        if isinstance(when,datetime.timedelta):
            return not dt%self.step
        elif isinstance(when,datetime.datetime):
            if self.end and when>self.end: return False
            if when<self.start: return False
            dt=when-self.start
            if not dt: return True
            if dt%self.step: return False # does not lie on a time step
            return True
        raise TypeError(f'{type(self).__name__}.__contains__ only understands datetime and timedelta objects.  You passed a f{type(when).__name__}.')

    def __iter__(self):
        time=self.start
        while time<=self.end:
            yield time
            time+=self.step

    def setnow(self,time):
        if time is None:
            self.__now=self.start
            return
        typecheck('time',time,datetime.datetime)
        if (time-self.start) % self.step:
            raise ValueError(
                f'{time} must be an integer multiple of {self.step} '
                f'after {self.start}')
        if self.end is not None and time>self.end:
            raise ValueError(
                f'{time} is after clock end time {self.end}')
        if time<self.start:
            raise ValueError(f'{time} is before clock start time {self.start}')
        self.__now=time
    def getnow(self):
        return self.__now
    now=property(getnow,setnow,None,'Current time on this clock.')

    def iternow(self):
        """!Sents the current time (self.now) to the start time, and
        iterates it over each possible time, yielding this object."""
        now=self.start
        while now<=self.end:
            self.now=now
            yield self
            now+=self.step

    def next(self,mul=1):
        return self.__now+self.step*mul

    def prior(self,mul=1):
        return self.__now+self.step*-mul

########################################################################

_SHELL_CLASS_MAP={ 'int':int, 'float':float, 'bool':bool, 'str':str }

def shell_to_python_type(arg):
    split=arg.split('::',1)
    if len(split)>1 and split[0] in CLASS_MAP:
        typename, strval=split
        if typename not in _SHELL_CLASS_MAP:
            raise ValueError(f'{arg}: unknown type {typename}')
        cls=_SHELL_CLASS_MAP[typename]
        return cls(strval)
    else:
        with suppress(ValueError): return int(arg)
        with suppress(ValueError): return float(arg)
        if arg.upper() in [ 'YES', 'TRUE' ]: return True
        if arg.upper() in [ 'NO', 'FALSE' ]: return False
        return arg
