from .MoabAlps import Scheduler as MoabAlpsScheduler

import math
import crow.tools as tools

__all__=['Scheduler']

class Scheduler(MoabAlpsScheduler):
    def __init__(self,settings,**kwargs):
        super().__init__(settings,**kwargs)
        self.rocoto_name='no'
