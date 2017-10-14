#!/bin/bash
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date: 2017-07-26 15:16:25 +0000 (Wed, 26 Jul 2017) $
# $Revision: 96049 $
# $Author: fanglin.yang@noaa.gov $
# $Id: fcst.sh 96049 2017-07-26 15:16:25Z fanglin.yang@noaa.gov $
###############################################################

###############################################################
## Author: Rahul Mahajan  Org: NCEP/EMC  Date: April 2017

## Abstract:
## Model forecast driver script
## EXPDIR : /full/path/to/config/files
## CDATE  : current analysis date (YYYYMMDDHH)
## CDUMP  : cycle name (gdas / gfs)
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
export DATA=$RUNDIR/$CDATE/$CDUMP/fcst
[[ -d $DATA ]] && rm -rf $DATA

cymd=$(echo $CDATE | cut -c1-8)
chh=$(echo  $CDATE | cut -c9-10)

# Default warm_start is OFF
export warm_start=".false."

# If RESTART conditions exist; warm start the model
# Restart conditions for GFS cycle come from GDAS
rCDUMP=$CDUMP
[[ $CDUMP = "gfs" ]] && rCDUMP="gdas"

if [ -f $ROTDIR/${rCDUMP}.$cymd/$chh/RESTART/${cymd}.${chh}0000.coupler.res ]; then
    export warm_start=".true."
    if [ $CDUMP = "gfs" ]; then
        mkdir -p $ROTDIR/${CDUMP}.$cymd/$chh/RESTART
        cd $ROTDIR/${CDUMP}.$cymd/$chh/RESTART
        $NCP $ROTDIR/${rCDUMP}.$cymd/$chh/RESTART/${cymd}.${chh}0000.* .
    fi
    if [ -f $ROTDIR/${CDUMP}.$cymd/$chh/${CDUMP}.t${chh}z.atminc.nc ]; then
        export read_increment=".true."
    else
        echo "WARNING: WARM START $CDUMP $CDATE WITHOUT READING INCREMENT!"
    fi
fi

# Forecast length for GFS forecast
if [ $CDUMP = "gfs" ]; then
    export FHMIN=$FHMIN_GFS
    export FHOUT=$FHOUT_GFS
    export FHMAX=$FHMAX_GFS
fi

###############################################################
# Run relevant exglobal script
$FORECASTSH
status=$?
[[ $status -ne 0 ]] && exit $status

###############################################################
# Convert model native history files to nemsio

export DATA=$ROTDIR/${CDUMP}.$cymd/$chh

if [ $CDUMP = "gdas" ]; then

    # Regrid 6-tile output to global array in NEMSIO gaussian grid for DA
    $REGRID_NEMSIO_SH
    status=$?
    [[ $status -ne 0 ]] && exit $status

elif [ $CDUMP = "gfs" ]; then

    # Remap 6-tile output to global array in NetCDF latlon
    $REMAPSH
    status=$?
    [[ $status -ne 0 ]] && exit $status

    # Convert NetCDF to nemsio
    $NC2NEMSIOSH
    status=$?
    [[ $status -ne 0 ]] && exit $status

fi

###############################################################
# Exit out cleanly
exit 0
