__all__=['to_dummy']

class ToDummy(object):
    def __init__(self,suite,apply_overrides):
        globals={ 'to_dummy':self,'metasched':self }
        self.type='dummy'
        self.suite=suite
        self.suite.update_globals(globals)
        if apply_overrides:
            self.suite.apply_overrides()

    def defenvar(self,name,value): return 'dummy'
    def datestring(self,name,value): return 'dummy'
    def defvar(self,name,value): return 'dummy'
    def varref(self,name): return 'dummy'
    def to_dummy(self): return 'dummy'

def to_dummy(suite,apply_overrides=True):
    return ToDummy(suite,apply_overrides=apply_overrides).to_dummy()
