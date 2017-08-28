from abc import abstractmethod

class Scheduler(object):
    @abstractmethod
    def rocoto_accounting(self,spec,indent): pass
    @abstractmethod
    def rocoto_resources(self,spec,indent): pass
    @abstractmethod
    def max_ranks_per_node(rank_spec): pass
    @abstractmethod
    def can_merge_ranks(rank_set_1,rank_set_2): pass
