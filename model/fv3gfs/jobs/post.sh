#!/bin/bash
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date: 2017-08-24 22:05:14 +0000 (Thu, 24 Aug 2017) $
# $Revision: 96869 $
# $Author: fanglin.yang@noaa.gov $
# $Id: post.sh 96869 2017-08-24 22:05:14Z fanglin.yang@noaa.gov $
###############################################################

###############################################################
## Author: Rahul Mahajan  Org: NCEP/EMC  Date: April 2017

## Abstract:
## NCEP post driver script
## EXPDIR : /full/path/to/config/files
## CDATE  : current analysis date (YYYYMMDDHH)
## CDUMP  : cycle name (gdas / gfs)
###############################################################

set -ex
JOBNAME=$( echo "$PBS_JOBNAME" | sed 's,/,.,g' )
( set -ue ; set -o posix ; set > $HOME/env-scan/$CDATE%$JOBNAME%set%before-to-sh ; env > $HOME/env-scan/$CDATE%$JOBNAME%env%before-to-sh )
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:workflow.$TASK_PATH.resource_env import:".*" )
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:workflow.$TASK_PATH from:shell_vars )
( set -ue ; set -o posix ; set > $HOME/env-scan/$CDATE%$JOBNAME%set%after-to-sh ; env > $HOME/env-scan/$CDATE%$JOBNAME%env%after-to-sh )
unset JOBNAME
echo just testing ; exit 0

###############################################################
# Set script and dependency variables
cymd=$(echo $CDATE | cut -c1-8)
chh=$(echo  $CDATE | cut -c9-10)

export COMROT=$ROTDIR/$CDUMP.$cymd/$chh

res=$(echo $CASE | cut -c2-)
export JCAP=$((res*2-2))
export LONB=$((4*res))
export LATB=$((2*res))

export pgmout="/dev/null" # exgfs_nceppost.sh.ecf will hang otherwise
export PREFIX="$CDUMP.t${chh}z."
export SUFFIX=".nemsio"

export DATA=$RUNDIR/$CDATE/$CDUMP/post
[[ -d $DATA ]] && rm -rf $DATA

# Run post job to create analysis grib files
export ATMANL=$ROTDIR/$CDUMP.$cymd/$chh/${PREFIX}atmanl$SUFFIX
if [ -f $ATMANL ]; then
    export ANALYSIS_POST="YES"
    $POSTJJOBSH
    status=$?
    [[ $status -ne 0 ]] && exit $status
fi

# Run post job to create forecast grib files
# Only for GFS cycles.
# We no longer do relocation, and thus GDAS cycle does not need forecast grib files
if [ $CDUMP = "gfs" ]; then
    export ANALYSIS_POST="NO"
    $POSTJJOBSH
    status=$?
    [[ $status -ne 0 ]] && exit $status
fi

###############################################################
# Exit out cleanly
exit 0
