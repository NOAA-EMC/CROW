#! /bin/sh

set -ue

PYTHONPATH=$( pwd )/../../${PYTHONPATH:+${PYTHONPATH}:}
TO_SH=../../to_sh.py

test -s $TO_SH
test -x $TO_SH

if [[ "${1:-missing}" == -v ]] ; then
    set -x
    TO_SH() {
        "$TO_SH" -v "$@"
    }
else
    TO_SH() {
        echo 1>&2
        echo "> $TO_SH" "$@" 1>&2
        "$TO_SH" "$@"
    }
fi

eval $( TO_SH test.yaml ONE=one )
echo "  ONE = 1 = ${ONE}"
unset ONE

eval $( TO_SH test.yaml FIVE=2**2+1 )
echo "  FIVE = 5 = ${FIVE}"
unset FIVE

eval $( TO_SH test.yaml scope:vars VARS_CAT=CAT )
echo "  VARS_CAT = Apollo = ${VARS_CAT}"
unset VARS_CAT

eval $( TO_SH test.yaml scope:array[2] I=item T=texture )
echo "  I = three = $I"
echo "  T = fluffy = $T"
unset I T

eval $( TO_SH test.yaml on=logical.TRUE_TEST scope:logical off=FALSE_TEST )
echo "  on = YES = $on"
echo "  off = NO = $off"
eval $( TO_SH test.yaml bool:.true.,.false. scope:logical \
            on=TRUE_TEST off=FALSE_TEST )
echo "  on = .true. = $on"
echo "  off = .false. = $off"
unset on off

eval $( TO_SH test.yaml scope:float SHORT_PI=short_pi ROUNDOFF_PI=too_long \
        float:%.20f LONG_PI=too_long NOT_FLOAT=not_float )
echo "  SHORT_PI = 3.14159 = $SHORT_PI"
echo "  floating point imprecision tests: of 3.141592653589793"
echo "    default format: $ROUNDOFF_PI"
echo "    %.20f   format: $LONG_PI"
echo "  NOT_FLOAT = 3 = $NOT_FLOAT"
unset SHORT_PI LONG_PI

TO_SH test.yaml expand:./test.nml
