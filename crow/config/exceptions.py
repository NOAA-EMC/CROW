__all__=['ConfigError', 'ConditionalMissingDoWhen', 'TemplateErrors',
         'CalcRecursionTooDeep', 'ExpandMissingResult',
         'CalcKeyError', 'TemplateError', 'InvalidConfigTemplate',
         'InvalidConfigValue', 'InvalidConfigType' ]

# module-specific exceptions:
class ConfigError(Exception): pass
class ConditionalMissingDoWhen(ConfigError): pass
class CalcRecursionTooDeep(ConfigError): pass
class ExpandMissingResult(ConfigError): pass
class CalcKeyError(ConfigError): pass
class TemplateError(ConfigError): pass
class InvalidConfigTemplate(TemplateError): pass
class InvalidConfigValue(TemplateError): pass
class InvalidConfigType(TemplateError): pass
class TemplateErrors(ConfigError):
    def __init__(self,errors):
        super().__init__(self,'\n'.join([ str(e) for e in errors ]))
        self.template_errors=list(errors)
