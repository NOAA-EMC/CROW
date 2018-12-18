#! /bin/bash
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date: 2017-10-30 18:48:54 +0000 (Mon, 30 Oct 2017) $
# $Revision: 98721 $
# $Author: fanglin.yang@noaa.gov $
# $Id: getic.sh 98721 2017-10-30 18:48:54Z fanglin.yang@noaa.gov $
###############################################################

###############################################################
## Author: Rahul Mahajan  Org: NCEP/EMC  Date: August 2017

## Abstract:
## Get GFS intitial conditions
## EXPDIR : /full/path/to/config/files
## CDATE  : current date (YYYYMMDDHH)
## CDUMP  : cycle name (gdas / gfs)
###############################################################

set -ex
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:platform.general_env import:".*" )
eval $( $HOMEcrow/to_sh.py $CONFIG_YAML export:y scope:workflow.$TASK_PATH from:shell_vars )

###############################################################
# Set script and dependency variables

yyyy=$(echo $CDATE | cut -c1-4)
mm=$(echo $CDATE | cut -c5-6)
dd=$(echo $CDATE | cut -c7-8)
hh=$(echo $CDATE | cut -c9-10)
cymd=$(echo $CDATE | cut -c1-8)

###############################################################

target_dir=$ICSDIR/$CDATE/$CDUMP
mkdir -p $target_dir
cd $target_dir

# Save the files as legacy EMC filenames
ftanal[1]="pgbanl.${CDUMP}.$CDATE"
ftanal[2]="siganl.${CDUMP}.$CDATE"
ftanal[3]="sfcanl.${CDUMP}.$CDATE"
ftanal[4]="nstanl.${CDUMP}.$CDATE"

# Initialize return code to 0
rc=1

if [ $ics_from = "opsgfs" ]; then

    # Handle nemsio and pre-nemsio GFS filenames
    if [ $CDATE -gt "2017072000" ]; then
        nfanal=4
        fanal[1]="./${CDUMP}.t${hh}z.pgrbanl"
        fanal[2]="./${CDUMP}.t${hh}z.atmanl.nemsio"
        fanal[3]="./${CDUMP}.t${hh}z.sfcanl.nemsio"
        fanal[4]="./${CDUMP}.t${hh}z.nstanl.nemsio"
        flanal="${fanal[1]} ${fanal[2]} ${fanal[3]} ${fanal[4]}"
        tarpref="gpfs_hps_nco_ops_com"
    else
        nfanal=3
        [[ $CDUMP = "gdas" ]] && str1=1
        fanal[1]="./${CDUMP}${str1}.t${hh}z.pgrbanl"
        fanal[2]="./${CDUMP}${str1}.t${hh}z.sanl"
        fanal[3]="./${CDUMP}${str1}.t${hh}z.sfcanl"
        flanal="${fanal[1]} ${fanal[2]} ${fanal[3]}"
        tarpref="com2"
    fi

    # First check the COMROOT for files, if present copy over
    if [ $machine = "WCOSS_C" ]; then

        # Need COMROOT
        module load prod_envir >> /dev/null 2>&1

        comdir="$COMROOT/$CDUMP/prod/$CDUMP.$cymd"
        rc=0
        for i in `seq 1 $nfanal`; do
            if [ -f $comdir/${fanal[i]} ]; then
                $NCP $comdir/${fanal[i]} ${ftanal[i]}
            else
                rb=1 ; ((rc+=rb))
            fi
        done

    fi

    # Get initial conditions from HPSS
    if [ $rc -ne 0 ]; then

        hpssdir="/NCEPPROD/hpssprod/runhistory/rh$yyyy/$yyyy$mm/$cymd"
        if [ $CDUMP = "gdas" ]; then
            tarball="$hpssdir/${tarpref}_gfs_prod_${CDUMP}.${CDATE}.tar"
        elif [ $CDUMP = "gfs" ]; then
            tarball="$hpssdir/${tarpref}_gfs_prod_${CDUMP}.${CDATE}.anl.tar"
        fi

        # check if the tarball exists
        hsi ls -l $tarball
        rc=$?
        if [ $rc -ne 0 ]; then
            echo "$tarball does not exist and should, ABORT!"
            exit $rc
        fi
        # get the tarball
        htar -xvf $tarball $flanal
        rc=$?
        if [ $rc -ne 0 ]; then
            echo "untarring $tarball failed, ABORT!"
            exit $rc
        fi

        # Move the files to legacy EMC filenames
        for i in `seq 1 $nfanal`; do
            if [[ "${fanal[i]}" != "${ftanal[i]}" ]] ; then
                $NMV ${fanal[i]} ${ftanal[i]}
            fi
        done

    fi

    # If found, exit out
    if [ $rc -ne 0 ]; then
        echo "Unable to obtain operational GFS initial conditions, ABORT!"
        exit 1
    fi

elif [ $ics_from = "pargfs" ]; then

    # Filenames in parallel
    nfanal=4
    fanal[1]="pgbanl.${CDUMP}.$CDATE"
    fanal[2]="gfnanl.${CDUMP}.$CDATE"
    fanal[3]="sfnanl.${CDUMP}.$CDATE"
    fanal[4]="nsnanl.${CDUMP}.$CDATE"
    flanal="${fanal[1]} ${fanal[2]} ${fanal[3]} ${fanal[4]}"

    # Get initial conditions from HPSS from retrospective parallel
    tarball="$HPSS_PAR_PATH/${CDATE}${CDUMP}.tar"

    # check if the tarball exists
    hsi ls -l $tarball
    rc=$?
    if [ $rc -ne 0 ]; then
        echo "$tarball does not exist and should, ABORT!"
        exit $rc
    fi
    # get the tarball
    htar -xvf $tarball $flanal
    rc=$?
    if [ $rc -ne 0 ]; then
        echo "untarring $tarball failed, ABORT!"
        exit $rc
    fi

    # Move the files to legacy EMC filenames
    for i in `seq 1 $nfanal`; do
        if [[ "${fanal[i]}" != "${ftanal[i]}" ]] ; then
            $NMV ${fanal[i]} ${ftanal[i]}
        fi
    done

    # If found, exit out
    if [ $rc -ne 0 ]; then
        echo "Unable to obtain parallel GFS initial conditions, ABORT!"
        exit 1
    fi

else

    echo "ics_from = $ics_from is not supported, ABORT!"
    exit 1

fi
###############################################################

# Copy pgbanl file to COMROT for verification
COMROT=$ROTDIR/${CDUMP}.$cymd/$hh
[[ ! -d $COMROT ]] && mkdir -p $COMROT
$NCP ${ftanal[1]} $COMROT/${CDUMP}.t${hh}z.pgrbanl

###############################################################
# Exit out cleanly
exit 0
