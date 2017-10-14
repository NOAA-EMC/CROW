#!/bin/bash
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date: 2017-08-16 21:42:24 +0000 (Wed, 16 Aug 2017) $
# $Revision: 96658 $
# $Author: fanglin.yang@noaa.gov $
# $Id: efcs.sh 96658 2017-08-16 21:42:24Z fanglin.yang@noaa.gov $
###############################################################

###############################################################
## Author: Rahul Mahajan  Org: NCEP/EMC  Date: April 2017

## Abstract:
## Ensemble forecast driver script
## EXPDIR : /full/path/to/config/files
## CDATE  : current analysis date (YYYYMMDDHH)
## CDUMP  : cycle name (gdas / gfs)
## ENSGRP : ensemble sub-group to make forecasts (1, 2, ...)
###############################################################

set -ex
JOBNAME=$( echo "$PBS_JOBNAME" | sed 's,/,.,g' )
( set -ue ; set -o posix ; set > $HOME/env-scan/$CDATE%$JOBNAME%set%before-to-sh ; env > $HOME/env-scan/$CDATE%$JOBNAME%env%before-to-sh )
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:workflow.$TASK_PATH.env all:".*" )
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:workflow.$TASK_PATH from:shell_vars )
( set -ue ; set -o posix ; set > $HOME/env-scan/$CDATE%$JOBNAME%set%after-to-sh ; env > $HOME/env-scan/$CDATE%$JOBNAME%env%after-to-sh )
unset JOBNAME
echo just testing ; exit 0

###############################################################
# Set script and dependency variables
export CASE=$CASE_ENKF
export DATA=$RUNDIR/$CDATE/$CDUMP/efcs.grp$ENSGRP
[[ -d $DATA ]] && rm -rf $DATA

# Get ENSBEG/ENSEND from ENSGRP and NMEM_EFCSGRP
ENSEND=$(echo "$NMEM_EFCSGRP * $ENSGRP" | bc)
ENSBEG=$(echo "$ENSEND - $NMEM_EFCSGRP + 1" | bc)
export ENSBEG=$ENSBEG
export ENSEND=$ENSEND

cymd=$(echo $CDATE | cut -c1-8)
chh=$(echo  $CDATE | cut -c9-10)

# Default warm_start is OFF
export warm_start=".false."

# If RESTART conditions exist; warm start the model
memchar="mem"`printf %03i $ENSBEG`
if [ -f $ROTDIR/enkf.${CDUMP}.$cymd/$chh/$memchar/RESTART/${cymd}.${chh}0000.coupler.res ]; then
    export warm_start=".true."
    if [ -f $ROTDIR/enkf.${CDUMP}.$cymd/$chh/$memchar/${CDUMP}.t${chh}z.atminc.nc ]; then
        export read_increment=".true."
    else
        echo "WARNING: WARM START $CDUMP $CDATE WITHOUT READING INCREMENT!"
    fi
fi

# Forecast length for EnKF forecast
export FHMIN=$FHMIN_ENKF
export FHOUT=$FHOUT_ENKF
export FHMAX=$FHMAX_ENKF

###############################################################
# Run relevant exglobal script
$ENKFFCSTSH
status=$?
[[ $status -ne 0 ]] && exit $status

###############################################################
# Double check the status of members in ENSGRP
EFCSGRP=$ROTDIR/enkf.${CDUMP}.$cymd/$chh/efcs.grp${ENSGRP}
if [ -f $EFCSGRP ]; then
    npass=$(grep "PASS" $EFCSGRP | wc -l)
else
    npass=0
fi
echo "$npass/$NMEM_EFCSGRP members successfull in efcs.grp$ENSGRP"
if [ $npass -ne $NMEM_EFCSGRP ]; then
    echo "ABORT!"
    cat $EFCSGRP
    exit 99
fi

###############################################################
# Exit out cleanly
exit 0
