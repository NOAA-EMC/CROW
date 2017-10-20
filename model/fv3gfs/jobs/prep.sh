#!/bin/bash
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date: 2017-08-16 21:42:24 +0000 (Wed, 16 Aug 2017) $
# $Revision: 96658 $
# $Author: fanglin.yang@noaa.gov $
# $Id: prep.sh 96658 2017-08-16 21:42:24Z fanglin.yang@noaa.gov $
###############################################################

###############################################################
## Author: Rahul Mahajan  Org: NCEP/EMC  Date: April 2017

## Abstract:
## Do prepatory tasks
## EXPDIR : /full/path/to/config/files
## CDATE  : current analysis date (YYYYMMDDHH)
## CDUMP  : cycle name (gdas / gfs)
###############################################################

set -ex
JOBNAME=$( echo "$PBS_JOBNAME" | sed 's,/,.,g' )
( set -ue ; set -o posix ; set > $HOME/env-scan/$CDATE%$JOBNAME%set%before-to-sh ; env > $HOME/env-scan/$CDATE%$JOBNAME%env%before-to-sh )
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML scope:workflow.$TASK_PATH from:Inherit )
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:workflow.$TASK_PATH from:shell_vars )
( set -ue ; set -o posix ; set > $HOME/env-scan/$CDATE%$JOBNAME%set%after-to-sh ; env > $HOME/env-scan/$CDATE%$JOBNAME%env%after-to-sh )
unset JOBNAME
echo just testing ; exit 0

###############################################################
# Set script and dependency variables

cymd=$(echo $CDATE | cut -c1-8)
chh=$(echo  $CDATE | cut -c9-10)

export OPREFIX="${CDUMP}.t${chh}z."

export COMIN_OBS="$DMPDIR/$CDATE/$CDUMP"
export COMOUT="$ROTDIR/$CDUMP.$cymd/$chh"
[[ ! -d $COMOUT ]] && mkdir -p $COMOUT

# Do relocation
if [ $DO_RELOCATE = "YES" ]; then
    $DRIVE_RELOCATESH
    echo "RELOCATION IS TURNED OFF in FV3, DRIVE_RELOCATESH does not exist, ABORT!"
    status=1
    [[ $status -ne 0 ]] && exit $status
fi

# Generate prepbufr files from dumps or copy from OPS
if [ $DO_MAKEPREPBUFR = "YES" ]; then
    $DRIVE_MAKEPREPBUFRSH
    [[ $status -ne 0 ]] && exit $status
else
    $NCP $COMIN_OBS/${OPREFIX}prepbufr               $COMOUT/${OPREFIX}prepbufr
    $NCP $COMIN_OBS/${OPREFIX}prepbufr.acft_profiles $COMOUT/${OPREFIX}prepbufr.acft_profiles
fi

###############################################################
# Exit out cleanly
exit 0
