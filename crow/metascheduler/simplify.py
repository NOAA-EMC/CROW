"""In-place simplification of dependency trees by applying rules of
boolean algebra.  Ensures short circuit assumptions still hold."""

import crow.config
from crow.config import OrDependency,AndDependency,NotDependency, \
    TRUE_DEPENDENCY, FALSE_DEPENDENCY, LogicalDependency
from crow.tools import typecheck

__all__=[ 'complexity', 'simplify' ]

def complexity(tree):
    if isinstance(tree,AndDependency) or isinstance(tree,OrDependency):
        return 1.2*sum([ complexity(dep) for dep in tree.depends ])
    elif isinstance(tree,NotDependency):
        return 1.2*complexity(tree.depend)
    return 1

def simplify(tree):
    typecheck('tree',tree,LogicalDependency)
    tree=tree.copy_dependencies()
    tree=simplify_no_de_morgan(tree)
    return de_morgan(tree)

def simplify_no_de_morgan(tree):
    # Apply all simplificatios except de morgan's law.  Called from
    # within de_morgan() to apply all other simplifications to the
    # result of de-morganing the tree.
    if isinstance(tree,OrDependency) or isinstance(tree,AndDependency):
        tree=simplify_sequence(tree)
    if isinstance(tree,NotDependency):
        tree.depend=simplify(tree.depend)
        if isinstance(tree.depend,NotDependency):
            return tree.depend.depend # not not x = x
        elif tree.depend==TRUE_DEPENDENCY:
            return FALSE_DEPENDENCY  # NOT true = false
        elif tree.depend==FALSE_DEPENDENCY:
            return TRUE_DEPENDENCY  # NOT false = true
    return tree

def de_morgan(tree):
    # Apply de morgan's law, choose least complex option.
    if not isinstance(tree,NotDependency): return tree
    dup=tree.copy_dependencies()
    if isinstance(dup.depend,AndDependency):
        # not ( x and y ) = (not x) or (not y)
        alternative=simplify_no_de_morgan(OrDependency(
            *[ NotDependency(dep) for dep in dup.depend.depends ]))
    elif isinstance(dup.depend,OrDependency):
        # not ( x or y ) = (not x) and (not y)
        alternative=simplify_no_de_morgan(AndDependency(
            *[ NotDependency(dep) for dep in dup.depend.depends ]))
    else: return tree
    if complexity(alternative)<complexity(tree):
        return alternative
    return tree

def simplify_sequence(dep):
    deplist=dep.depends
    cls=type(dep)
    is_or = isinstance(dep,OrDependency)

    # Simplify and merge subexpressions.
    expanded=True
    while expanded:
        expanded=False
        i=0

        # simplify each subexpression
        for i in range(len(deplist)):
            deplist[i]=simplify(deplist[i])

        # A & (B & C) = A & B & C
        # A | (B | C) = A | B | C
        while i<len(deplist):
            if type(deplist[i]) == type(dep):
                deplist=deplist[0:i]+deplist[i].depends+deplist[i+1:]
                expanded=True
            elif ( isinstance(deplist[i],AndDependency) or \
                   isinstance(deplist[i],OrDependency) ) and \
                  i>0 and type(deplist[i])==type(deplist[i-1]):
                deplist[i-1].depends+=deplist[i].depends
                del deplist[i]
                expanded=True
            else:
                i=i+1

    i=0
    while i<len(deplist):
        assert(deplist)
        if len(deplist)==1:
            return deplist[0]
        elif deplist[i]==TRUE_DEPENDENCY:
            if is_or: return deplist[i] # A|true = true
            del deplist[i] # A&true = A
        elif deplist[i]==FALSE_DEPENDENCY:
            if not is_or: return deplist[i] # A&false = false
            del deplist[i] # A|false = A
        else:
            j=i+1
            remove_i=False
            while j<len(deplist):
                if deplist[i]==deplist[j]:
                    del deplist[j]
                elif not is_or and isinstance(deplist[j],NotDependency) and \
                     deplist[j].depend==deplist[i]:
                    return FALSE_DEPENDENCY
                else:
                    j=j+1
            if len(deplist)==1:
                return deplist[0]
            i=i+1

    return cls(*deplist)

def test():
    from datetime import timedelta
    DEP1=crow.config.CycleExistsDependency(timedelta())
    DEP2=crow.config.CycleExistsDependency(timedelta(seconds=3600))
    DEP3=crow.config.CycleExistsDependency(timedelta(seconds=7200))

    assert(abs(complexity(DEP1|DEP2)-2.4)<1e-3)
    assert(abs(complexity(DEP1&DEP2)-2.4)<1e-3)
    assert(abs(complexity(~(DEP1&DEP2))-2.88)<1e-3)

    assert(simplify(~DEP1 | DEP1)==TRUE_DEPENDENCY)
    assert(simplify(~DEP1 & DEP1)==FALSE_DEPENDENCY)
    assert(simplify(~(~DEP1 | ~DEP2)) == DEP1&DEP2)
    assert(simplify(~DEP2 & ~(~DEP1 | ~DEP2)) == FALSE_DEPENDENCY)
