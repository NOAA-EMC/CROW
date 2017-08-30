import logging
import os
from abc import abstractmethod
from collections import UserList, Mapping, Sequence, OrderedDict
from subprocess import Popen, PIPE, CompletedProcess

__all__=['ShellCommand']

logger=logging.getLogger('crow')

class ShellCommand(object):
    def __init__(self,command,env=False,files=False,cwd=False):
        if isinstance(command,str):
            self.command=[ '/bin/sh', '-c', command ]
        elif isinstance(command,Sequence) and not isinstance(command,bytes):
            self.command=[ str(s) for s in command ]
        else:
            raise TypeError('command must be a string or list, not a '+
                            type(s).__name__)

        self.command=command
        self.env=None
        if env:
            self.env=dict(os.environ)
            self.env.update(env)
        self.files=OrderedDict()
        self.cwd=cwd or None

        if not files: return # nothing more to do

        for f in files:
            self.files[f['name']]=f
            
    def __str__(self):
        return f'{type(self).__name__}(command={self.command}, ' + \
          f'env={self.env!r}, cwd={self.cwd!r}, files=[ ' + \
          ', '.join([ repr(v) for k,v in self.files.items() ]) + '])'
        
    def run(self,input=None,stdin=None,stdout=None,stderr=None,timeout=None,
            check=False,encoding=None):
        """!Runs this command via subprocess.Pipe.  Returns a
        CompletedProcess.  Arguments have the same meaning as
        subprocess.run.        """
        for name,f in self.files.items():
            mode=f.get('mode','wt')
            logger.info(f'{f["name"]}: write mode {mode}')
            with open(f['name'],mode) as fd:
                fd.write(str(f['content']))

        logger.info(f'Popen {repr(self.command)}')
        pipe=Popen(args=self.command,stdin=stdin,stdout=stdout,
                   stderr=stderr,encoding=encoding,
                   cwd=self.cwd,env=self.env)
        (stdout, stderr) = pipe.communicate(input=input,timeout=timeout)
        cp=CompletedProcess(self.command,pipe.returncode,stdout,stderr)
        if check:
            cp.check_returncode()
        return cp
