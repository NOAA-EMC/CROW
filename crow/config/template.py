"""!Validation logic for YAML mapping types via the "!Template" YAML
type.

@note Intermediate python concepts in use

To develop or understand this file, you must be fluent in the
following intermediate Python concepts:

- treating types as objects
- treating functions as objects

"""

from copy import copy
from datetime import timedelta, datetime
from crow.config.exceptions import *
from crow.config.eval_tools import list_eval, dict_eval, multidict, from_config
from crow.config.represent import GenericList, GenericDict, GenericOrderedDict

class Template(dict_eval):
    """!Internal implementation of the YAML Template type.  Validates a
    dict_eval, inserting defaults and reporting errors via the
    TemplateErrors exception.    """
    def _check_scope(self,scope,stage):
        checked=set()
        errors=list()
        template=copy(self)
        did_something=True

        # Main validation loop.  Iteratively validate, adding new
        # Templates as they become available via is_present.
        while did_something:
            did_something=False
            assert(hasattr(template,'_check_scope'))

            # Inner validation loop.  Validate based on all Templates
            # found thus far.  Add new templates if found via
            # is_present.  Run prechecks if present
            for var in set(scope)-checked:
                if var not in template: continue
                try:
                    did_something=True
                    checked.add(var)
                    scheme=template[var]

                    if stage and 'stages' in scheme:
                        if stage not in scheme.stages:
                            continue # skip validation; wrong stage
                    elif 'stages' in scheme:
                        continue # skip validation of stage-specific schemes

                    if 'precheck' in scheme:
                        scope[var]=scheme.precheck

                    validate_var(scope._path,scheme,var,scope[var])
                    if 'if_present' in scheme:
                        ip=from_config(
                            var,scheme._raw('if_present'),self._globals(),scope)
                        if not ip: continue
                        new_template=Template(ip._raw_child())
                        new_template.update(template)
                        template=new_template
                except (IndexError,AttributeError) as pye:
                    errors.append(f'{scope._path}.{var}: {pye}')
                except ConfigError as ce:
                    errors.append(str(ce))

        # Insert default values for all templates found thus far and
        # detect any missing, non-optional, variables
        missing=list()
        for var in template:
            if var not in scope:
                tmpl=template[var]
                if not hasattr(tmpl,'__getitem__') or not hasattr(tmpl,'update'):
                    raise TypeError(f'{self._path}.{var}: All entries in a !Template must be maps not {type(tmpl).__name__}')
                if 'default' in tmpl:
                    try:
                        did_something=True
                        scope[var]=tmpl._raw('default')
                    except AttributeError:
                        scope[var]=tmpl['default']
                elif not tmpl.get('optional',False):
                    missing.append(var)
        if missing:
            raise VariableMissing(f'{scope._path}: missing: '+
                                  ', '.join(missing))

        # Override any variables if requested via "override" clauses.
        for var in template:
            if var in scope and 'override' in template[var]:
                override=template[var].override
                if override is not None: scope[var]=override

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
        'seq':[set,list,tuple,list_eval,GenericList],
        'timedelta':[timedelta],'datetime':[datetime] }

## @var VALIDATORS
# Mapping from YAML type to validation function.
VALIDATORS={ 'map':validate_dict,     
             'seq':validate_list,
             'list':validate_list,
             'set':validate_list,
             'int':validate_scalar,
             'bool':validate_scalar,
             'string':validate_scalar,
             'datetime':validate_scalar,
             'float':validate_scalar,
             'timedelta': validate_scalar}

def validate_type(path,var,typ,val,allowed):
    """!Top-level validation function.  Checks that the value val of the
    variable var is of the given type typ and has values in the list
    of those allowed.    """
    types=typ.split()
    for t in types:
        if t not in VALIDATORS:
            raise InvalidConfigType(
                f'{path}.{var}={t!r}: unknown type in {typ!r}')
    result=VALIDATORS[types[-1]](types[:-1],val,allowed,types[-1])
    if result is UNKNOWN_TYPE:
        raise InvalidConfigType(
            f'{path}.{var}={t!r}: unknown type in {typ!r}')
    elif result is TYPE_MISMATCH:
        val_repr='null' if val is None else repr(val)
        raise InvalidConfigValue(
            f'{path}.{var}={val_repr}: not valid for type {typ!r}')
    elif result is NOT_ALLOWED:
        val_repr='null' if val is None else repr(val)
        raise InvalidConfigValue(
            f'{path}.{var}={val_repr}: not an allowed value ('
            f'{", ".join([repr(s) for s in allowed])})')

def validate_var(path,scheme,var,val):
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
    validate_type(path,var,typ,val,allowed)

