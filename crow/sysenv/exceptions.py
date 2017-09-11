from crow.exceptions import CROWException
class SysEnvConfigError(CROWException): pass
class MachineTooSmallError(SysEnvConfigError): pass
class UnknownParallelismError(SysEnvConfigError): pass
class UnknownSchedulerError(SysEnvConfigError): pass
class InvalidJobResourceSpec(SysEnvConfigError): pass
