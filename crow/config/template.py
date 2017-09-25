"""!Validation logic for YAML mapping types via the "!Template" YAML
type.

@note Intermediate python concepts in use

To develop or understand this file, you must be fluent in the
following intermediate Python concepts:

- treating types as objects
- treating functions as objects

"""

from crow.config.exceptions import *
from crow.config.eval_tools import list_eval, dict_eval, multidict, from_config
from crow.config.represent import GenericList, GenericDict, GenericOrderedDict

class Template(dict_eval):
    """!Internal implementation of the YAML Template type.  Validates a
    dict_eval, inserting defaults and reporting errors via the
    TemplateErrors exception.    """
    def _check_scope(self,scope):
        checked=set()
        errors=list()
        template=dict(self)
        did_something=True

        # Main validation loop.  Iteratively validate, adding new
        # Templates as they become available via is_present.
        while did_something:
            did_something=False

            # Inner validation loop.  Validate based on all Templates
            # found thus far.  Add new templates if found via
            # is_present.
            for var in set(scope)-checked:
                if var not in template: continue
                try:
                    did_something=True
                    checked.add(var)
                    scheme=template[var]

                    if 'precheck' in scheme:
                        scope[var]=scheme.precheck
                        
                    validate_var(scheme,var,scope[var])
                    if 'if_present' in scheme:
                        ip=from_config(
                            var,scheme._raw('if_present'),self._globals(),scope)
                        if not ip: continue
                        new_template=dict(ip)
                        new_template.update(template)
                        template=new_template
                except ConfigError as ce:
                    errors.append(ce)
                    raise

        # Insert default values for all templates found thus far and
        # override values if requested:
        for var in template:
            if var not in scope:
                tmpl=template[var]
                if 'default' in tmpl:
                    try:
                        did_something=True
                        scope[var]=tmpl._raw('default')
                    except AttributeError:
                        scope[var]=tmpl['default']
                if 'override' in tmpl:
                    scope[var]=tmpl.override

        if errors: raise TemplateErrors(errors)

class TemplateValidationFailed(object):
    """!Used for constants that represent validation failure cases"""
    def __bool__(self):         return False

NOT_ALLOWED=TemplateValidationFailed()
TYPE_MISMATCH=TemplateValidationFailed()
UNKNOWN_TYPE=TemplateValidationFailed()

def validate_scalar(types,val,allowed,tname):
    """!Validates val against the type tname, and allowed values.  Forbids
    recursion (scalars cannot contain subobjects."""
    if allowed and val not in allowed:    return NOT_ALLOWED
    if len(types):                        return TYPE_MISMATCH
    for cls in TYPES[tname]:
        if isinstance(val,cls): return True
    return TYPE_MISMATCH

def validate_list(types,val,allowed,tname):
    """!Valdiates that val is a list that contains the specified allowed
    values.  Recurses into subobjects, which must be of type types[-1] """
    if not len(types):                     return TYPE_MISMATCH
    if type(val) not in TYPES[tname]: raise Exception('unknown type')
    for v in val:
        result=VALIDATORS[types[-1]](types[:-1],v,allowed,types[-1])
        if not result: return result
    return True

def validate_dict(types,val,allowed,typ):
    """!Valdiates that val is a map that contains the specified allowed
    values.  Recurses into subobjects, which must be of type types[-1] """
    if not len(types):                    return TYPE_MISMATCH
    if str(type(val)) not in typ['list']: raise(Exception('unknown type'))
    for k,v in val.items():
        result=VALIDATORS[types[-1]](types[:-1],v,allowed,types[-1])
        if not result: return result
    return True

## @var TYPES
# Mapping from YAML type to valid python types.
TYPES={ 'int':[int], 'bool':[bool], 'string':[str,bytes],
        'float':[float], 'list':[set,list,tuple,list_eval,GenericList],
        'dict':[dict,dict_eval,GenericDict,GenericOrderedDict],
        'seq':[set,list,tuple,list_eval,GenericList] }

## @var VALIDATORS
# Mapping from YAML type to validation function.
VALIDATORS={ 'map':validate_dict,     
             'seq':validate_list,
             'list':validate_list,
             'set':validate_list,
             'int':validate_scalar,
             'bool':validate_scalar,
             'string':validate_scalar,
             'float':validate_scalar }

def validate_type(var,typ,val,allowed):
    """!Top-level validation function.  Checks that the value val of the
    variable var is of the given type typ and has values in the list
    of those allowed.    """
    types=typ.split()
    for t in types:
        if t not in VALIDATORS:
            raise InvalidConfigType('%s=%s: unknown type in %s'%(
                str(var),repr(t),repr(typ)))
    result=VALIDATORS[types[-1]](types[:-1],val,allowed,types[-1])
    if result is UNKNOWN_TYPE:
        raise InvalidConfigType('%s: type %s: unknown type in %s'%(
            str(var),repr(t),repr(typ)))
    elif result is TYPE_MISMATCH:
        raise InvalidConfigValue('%s=%s: not valid for type %s'%(
            str(var),repr(val),repr(typ)))
    elif result is NOT_ALLOWED:
        raise InvalidConfigValue('%s=%s: not an allowed value (%s)'%(
            str(var),repr(val),', '.join([repr(s) for s in allowed])))

def validate_var(scheme,var,val):
    """!Main entry point to recursive validation system.  Validates
    variable var with value val against the YAML Template list item in
    scheme.    """
    if 'type' not in scheme:
        raise InvalidConfigTemplate(var+'.type: missing')
    typ=scheme.type
    if not isinstance(typ,str):
        raise InvalidConfigTemplate(var+'.type: must be a string')
    allowed=scheme.get('allowed',[])
    if not isinstance(allowed,list) and not isinstance(allowed,list_eval):
        raise InvalidConfigTemplate(var+'.allowed: must be a list')
    validate_type(var,typ,val,allowed)
