#! /bin/sh

export PYTHONPATH=../../${PYTHONPATH:+:$PYTHONPATH}

set -eu

./shell_prep.py

crow_deliver() {
    flow="$1"
    format="$2"
    cycle="$3"
    actor="$4"
    shift 4
    ../../crow_dataflow_deliver_sh.py -v "$flow" "$format" test.db "$cycle" "$actor" "$@"
}

crow_find() {
    flow="$1"
    shift
    ../../crow_dataflow_find_sh.py -v "$flow" test.db "$@"
}

crow_find -o |\
while [[ 1 == 1 ]] ; do
    read flow actor slot meta
    if [[ "$?" != 0 ]] ; then
        break
    fi
    echo "($flow) ($actor) ($slot) ($meta)"
done
