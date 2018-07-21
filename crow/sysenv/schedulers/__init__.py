from crow.sysenv.exceptions import UnknownSchedulerError
from crow.sysenv.schedulers.MoabTorque import Scheduler as MoabTorqueScheduler
from crow.sysenv.schedulers.MoabAlps import Scheduler as MoabAlpsScheduler
from crow.sysenv.schedulers.MoabAlpsSh import Scheduler as MoabAlpsShScheduler
from crow.sysenv.schedulers.LSFAlps import Scheduler as LSFAlpsScheduler
from crow.sysenv.schedulers.LSF import Scheduler as LSFScheduler

KNOWN_SCHEDULERS={
    'MoabTorque': MoabTorqueScheduler,
    'MoabAlps': MoabAlpsScheduler,
    'MoabAlpsSh': MoabAlpsShScheduler,
    'LSFAlps': LSFAlpsScheduler,
    'LSF': LSFScheduler
    }

def get_scheduler(name,settings):
    if name not in KNOWN_SCHEDULERS:
        raise UnknownSchedulerError(name)
    cls=KNOWN_SCHEDULERS[name]
    return cls(settings)

def has_scheduler(name):
    return name in KNOWN_SCHEDULERS
