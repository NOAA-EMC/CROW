#! /bin/sh

set -xue

INFILE="$1"
MIN_SIZE="$2"
MIN_AGE="$3"
SLEEP_WAIT="$4"
MAX_WAIT_STEPS="$5"

while [[ "$waits" -lt "$MAX_WAIT_STEPS" ]] ; do
    mtime=$( stat -c %Y "$INFILE" )
    now=$( date +%s )
    age=$(( mtime - now ))
    size=$( stat -c %s "$INFILE" )
    if [[ "$size" -gt "$MIN_SIZE" && "$age" -gt "$MIN_AGE" ]] ; then
        echo "$INFILE: found."
    fi
    echo "$INFILE: still waiting..."
    sleep "$SLEEP_WAIT"
done

echo "$INFILE: timeout."
exit 1
