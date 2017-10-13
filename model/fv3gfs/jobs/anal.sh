#!/bin/bash
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date: 2017-08-16 21:42:24 +0000 (Wed, 16 Aug 2017) $
# $Revision: 96658 $
# $Author: fanglin.yang@noaa.gov $
# $Id: anal.sh 96658 2017-08-16 21:42:24Z fanglin.yang@noaa.gov $
###############################################################

###############################################################
## Author: Rahul Mahajan  Org: NCEP/EMC  Date: April 2017

## Abstract:
## Analysis driver script
## EXPDIR : /full/path/to/config/files
## CDATE  : current analysis date (YYYYMMDDHH)
## CDUMP  : cycle name (gdas / gfs)
###############################################################

# CONFIG_SCOPE=gfs.fcst.Perform
export CROW2SH="$CROW/to_sh.py scope:$CONFIG_SCOPE"

eval $( $CROWSH SHELL_VARNAME=YAML_VARNAME \
                import:"DOG_[0-9]+" )  # DOG_03 DOG_1 DOG_12345

# YAML action panel:
# some_action: !Action
#     ... variables ...
#     var1: val1
#     var2: val2
#     var3: val3
#     env_export: [ var1, var2, var3 ]
#

eval $( $CROWSH from:doc.action.some_action.env_export )

###############################################################
# !! Getting rid of these !!
# Source relevant configs
#configs="base anal"
#for config in $configs; do
#    . $EXPDIR/config.${config}
#    status=$?
#    [[ $status -ne 0 ]] && exit $status
#done

###############################################################
# Source machine runtime environment
. $BASE_ENV/${machine}.env anal
status=$?
[[ $status -ne 0 ]] && exit $status

###############################################################
# Set script and dependency variables
export GDATE=$($NDATE -$assim_freq $CDATE)

cymd=$(echo $CDATE | cut -c1-8)
chh=$(echo  $CDATE | cut -c9-10)
gymd=$(echo $GDATE | cut -c1-8)
ghh=$(echo  $GDATE | cut -c9-10)

export OPREFIX="${CDUMP}.t${chh}z."
export GPREFIX="gdas.t${ghh}z."
export GSUFFIX=".nemsio"
export APREFIX="${CDUMP}.t${chh}z."
export ASUFFIX=".nemsio"

export COMIN_OBS="$DMPDIR/$CDATE/$CDUMP"
export COMIN_GES="$ROTDIR/gdas.$gymd/$ghh"
export COMIN_GES_ENS="$ROTDIR/enkf.gdas.$gymd/$ghh"
export COMOUT="$ROTDIR/$CDUMP.$cymd/$chh"
export DATA="$RUNDIR/$CDATE/$CDUMP/anal"
[[ -d $DATA ]] && rm -rf $DATA

export ATMGES="$COMIN_GES/${GPREFIX}atmf006${GSUFFIX}"
if [ ! -f $ATMGES ]; then
    echo "FILE MISSING: ATMGES = $ATMGES"
    exit 1
fi
if [ $DOHYBVAR = "YES" ]; then
    export ATMGES_ENSMEAN="$COMIN_GES_ENS/${GPREFIX}atmf006.ensmean$GSUFFIX"
    if [ ! -f $ATMGES_ENSMEAN ]; then
        echo "FILE MISSING: ATMGES_ENSMEAN = $ATMGES_ENSMEAN"
        exit 2
    fi
fi

# Background resolution
export JCAP=$($NEMSIOGET $ATMGES jcap | awk '{print $2}')
status=$?
[[ $status -ne 0 ]] && exit $status
export LONB=$($NEMSIOGET $ATMGES dimx | awk '{print $2}')
status=$?
[[ $status -ne 0 ]] && exit $status
export LATB=$($NEMSIOGET $ATMGES dimy | awk '{print $2}')
status=$?
[[ $status -ne 0 ]] && exit $status
export LEVS=$($NEMSIOGET $ATMGES dimz | awk '{print $2}')
status=$?
[[ $status -ne 0 ]] && exit $status

if [ $DOHYBVAR = "YES" ]; then
    # Ensemble resolution
    export JCAP_ENKF=$($NEMSIOGET $ATMGES_ENSMEAN jcap | awk '{print $2}')
    status=$?
    [[ $status -ne 0 ]] && exit $status
    export LONB_ENKF=$($NEMSIOGET $ATMGES_ENSMEAN dimx | awk '{print $2}')
    status=$?
    [[ $status -ne 0 ]] && exit $status
    export LATB_ENKF=$($NEMSIOGET $ATMGES_ENSMEAN dimy | awk '{print $2}')
    status=$?
    [[ $status -ne 0 ]] && exit $status
fi

# Analysis resolution
if [ $DOHYBVAR == "YES" ]; then
    export JCAP_A=$JCAP_ENKF
    export LONA=$LONB_ENKF
    export LATA=$LATB_ENKF
else
    export JCAP_A=$JCAP
    export LONA=$LONB
    export LATA=$LATB
fi

# Link observational data
export PREPQC=${COMOUT}/${OPREFIX}prepbufr
export PREPQCPF=${COMOUT}/${OPREFIX}prepbufr.acft_profiles

###############################################################
# Run relevant exglobal script
$ANALYSISSH
status=$?
[[ $status -ne 0 ]] && exit $status

###############################################################
# Exit out cleanly
exit 0
