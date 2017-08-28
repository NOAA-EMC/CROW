from crow.sysenv.exceptions import UnknownParallelismError
import crow.sysenv.parallelism.HydraIMPI
from crow.sysenv.parallelism.HydraIMPI \
    import Parallelism as HydraIMPIParallelism

KNOWN_PARALLELISM={
    'HydraIMPI': HydraIMPIParallelism
    }

def get_parallelism(name,settings):
    if name not in KNOWN_PARALLELISM:
        raise UnknownParallelismError(name)
    cls=KNOWN_PARALLELISM[name]
    return cls(settings)

def has_parallelism(name):
    return name in KNOWN_PARALLELISM
