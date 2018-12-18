#! /bin/bash
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date: 2017-10-30 18:48:54 +0000 (Mon, 30 Oct 2017) $
# $Revision: 98721 $
# $Author: fanglin.yang@noaa.gov $
# $Id: eobs.sh 98721 2017-10-30 18:48:54Z fanglin.yang@noaa.gov $
###############################################################

###############################################################
## Author: Rahul Mahajan  Org: NCEP/EMC  Date: April 2017

## Abstract:
## EnKF innovations for ensemble mean driver script
## EXPDIR : /full/path/to/config/files
## CDATE  : current analysis date (YYYYMMDDHH)
## CDUMP  : cycle name (gdas / gfs)
###############################################################

set -ex
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:platform.general_env import:".*" )
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:workflow.$TASK_PATH from:Inherit )
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:workflow.$TASK_PATH from:shell_vars )
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:workflow.$TASK_PATH bool:.true.,.false. from:true_false_vars )
unset DELTIM

###############################################################
# Set script and dependency variables
export GDATE=$($NDATE -$assim_freq $CDATE)

cymd=$(echo $CDATE | cut -c1-8)
chh=$(echo  $CDATE | cut -c9-10)
gymd=$(echo $GDATE | cut -c1-8)
ghh=$(echo  $GDATE | cut -c9-10)

export OPREFIX="${CDUMP}.t${chh}z."
export APREFIX="${CDUMP}.t${chh}z."
export ASUFFIX=".nemsio"
export GPREFIX="${CDUMP}.t${ghh}z."
export GSUFFIX=".nemsio"

export COMIN_GES="$ROTDIR/$CDUMP.$gymd/$ghh"
export COMIN_ANL="$ROTDIR/$CDUMP.$cymd/$chh"
export COMIN_GES_ENS="$ROTDIR/enkf.$CDUMP.$gymd/$ghh"
export COMOUT="$ROTDIR/enkf.$CDUMP.$cymd/$chh"
export DATA="$RUNDIR/$CDATE/$CDUMP/eobs"
[[ -d $DATA ]] && rm -rf $DATA

export ATMGES_ENSMEAN="$COMIN_GES_ENS/${GPREFIX}atmf006.ensmean$GSUFFIX"
if [ ! -f $ATMGES_ENSMEAN ]; then
    echo "FILE MISSING: ATMGES_ENSMEAN = $ATMGES_ENSMEAN"
    exit 2
fi

export LEVS=$($NEMSIOGET $ATMGES_ENSMEAN dimz | awk '{print $2}')
status=$?
[[ $status -ne 0 ]] && exit $status

# Link observational data
export PREPQC="$COMIN_ANL/${OPREFIX}prepbufr"
export PREPQCPF="$COMIN_ANL/${OPREFIX}prepbufr.acft_profiles"

# Guess Bias correction coefficients related to control
export GBIAS=${COMIN_GES}/${GPREFIX}abias
export GBIASPC=${COMIN_GES}/${GPREFIX}abias_pc
export GBIASAIR=${COMIN_GES}/${GPREFIX}abias_air
export GRADSTAT=${COMIN_GES}/${GPREFIX}radstat

# Bias correction coefficients related to ensemble mean
export ABIAS="$COMOUT/${APREFIX}abias.ensmean"
export ABIASPC="$COMOUT/${APREFIX}abias_pc.ensmean"
export ABIASAIR="$COMOUT/${APREFIX}abias_air.ensmean"
export ABIASe="$COMOUT/${APREFIX}abias_int.ensmean"

# Diagnostics related to ensemble mean
export GSISTAT="$COMOUT/${APREFIX}gsistat.ensmean"
export CNVSTAT="$COMOUT/${APREFIX}cnvstat.ensmean"
export OZNSTAT="$COMOUT/${APREFIX}oznstat.ensmean"
export RADSTAT="$COMOUT/${APREFIX}radstat.ensmean"

# Select observations based on ensemble mean
export RUN_SELECT="YES"
export USE_SELECT="NO"
export SELECT_OBS="$COMOUT/${APREFIX}obsinput.ensmean"

export DIAG_SUFFIX="_ensmean"

# GSI namelist options specific to eobs
export SETUP_INVOBS="passive_bc=.false."

# Over-write variables
COMIN_GES_SAVE=$COMIN_GES
GSUFFIX_SAVE=$GSUFFIX
export COMIN_GES=$COMIN_GES_ENS
export GSUFFIX=".ensmean$GSUFFIX"

# Do not run global_cycle for ensemble mean
export DOGCYCLE="NO"

###############################################################
# Ensure clean stat tarballs for ensemble mean
for fstat in $CNVSTAT $OZNSTAT $RADSTAT; do
    [[ -f $fstat ]] && rm -f $fstat
done

###############################################################
# Run relevant exglobal script
$INVOBSSH
status=$?
[[ $status -ne 0 ]] && exit $status

###############################################################
# Exit out cleanly
exit 0
