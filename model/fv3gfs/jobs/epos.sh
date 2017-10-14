#!/bin/bash
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date: 2017-08-16 21:42:24 +0000 (Wed, 16 Aug 2017) $
# $Revision: 96658 $
# $Author: fanglin.yang@noaa.gov $
# $Id: epos.sh 96658 2017-08-16 21:42:24Z fanglin.yang@noaa.gov $
###############################################################

###############################################################
## Author: Rahul Mahajan  Org: NCEP/EMC  Date: April 2017

## Abstract:
## Ensemble post-processing driver script
## EXPDIR : /full/path/to/config/files
## CDATE  : current analysis date (YYYYMMDDHH)
## CDUMP  : cycle name (gdas / gfs)
###############################################################

set -e
JOBNAME=$( echo "$PBS_JOBNAME" | sed 's,/,.,g' )
( set -ue ; set -o posix ; set > $HOME/env-scan/$CDATE%$JOBNAME%set%before-to-sh ; env > $HOME/env-scan/$CDATE%$JOBNAME%env%before-to-sh )
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:workflow.$TASK_PATH.env all:".*" )
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:workflow.$TASK_PATH from:shell_vars )
( set -ue ; set -o posix ; set > $HOME/env-scan/$CDATE%$JOBNAME%set%after-to-sh ; env > $HOME/env-scan/$CDATE%$JOBNAME%env%after-to-sh )
unset JOBNAME
echo just testing ; exit 0

###############################################################
# Set script and dependency variables
cymd=$(echo $CDATE | cut -c1-8)
chh=$(echo  $CDATE | cut -c9-10)

export PREFIX="${CDUMP}.t${chh}z."
export SUFFIX=".nemsio"

export COMIN="$ROTDIR/enkf.$CDUMP.$cymd/$chh"
export COMOUT="$ROTDIR/enkf.$CDUMP.$cymd/$chh"
export DATA="$RUNDIR/$CDATE/$CDUMP/epos"
[[ -d $DATA ]] && rm -rf $DATA

###############################################################
# Run relevant exglobal script
$ENKFPOSTSH
status=$?
[[ $status -ne 0 ]] && exit $status

###############################################################
# Exit out cleanly
exit 0
