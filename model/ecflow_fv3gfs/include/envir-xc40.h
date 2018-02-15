# envir-xc40.h
export job=${job:-$LSB_JOBNAME} #Can't use $job in filenames!
export jobid=${jobid:-$job.$LSB_JOBID}

export envir=prod
export RUN_ENVIR=para
export SENDDBN=${SENDDBN:-%SENDDBN:YES%}
export SENDDBN_NTC=${SENDDBN_NTC:-%SENDDBN_NTC:YES%}

module load prod_envir prod_util

case $envir in
  prod)
    export CRAY_F_SET=hps2
    export EMCPEN=${EMCPEN:-%EMCPEN:ecfgfsfv3%}
    export jlogfile=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/com/jlogfile
    export DATAROOT=${DATAROOT:-/gpfs/${CRAY_F_SET}/stmp/emc.glopara/%EMCPEN%}
    export DBNROOT=${UTILROOT}/fakedbn
#    export NWROOT=/gpfs/hps3/emc/global/noscrub/emc.glopara/svn/gfs/q3fy17_final
####    export NWROOT=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/fv3/git/fv3gfs
####    export NWROOT=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/fv3/git/master_20180113
    export NWROOT=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/fv3/git/fv3gfs_flat
    export NWPROD=/gpfs/hps/nco/ops/nwprod
    export COMROOT=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/com
    export COMOUT_ROOT=$COMROOT
    export PCOMROOT=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/pcom/prod
    export GESROOT=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/nwges
    export GESROOThps=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/nwges
    export GESROOTp1=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/nwges
    export GESROOTp2=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/nwges
    export KEEPDATA=NO
####    export HOMEobsproc_dump=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/obsproc_dump.v4.0.0
####    export HOMEobsproc_shared_bufr_dumplist=/gpfs/hps/nco/ops/nwprod/obsproc_shared/bufr_dumplist.v1.3.0
    ;;
  emcpara)
    export CRAY_F_SET=hps2
    export EMCPEN=${EMCPEN:-%EMCPEN:ecfgfs2017%}
    export jlogfile=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/com/jlogfile
    export DATAROOT=${DATAROOT:-/gpfs/${CRAY_F_SET}/stmp/emc.glopara/%EMCPEN%}
    export DBNROOT=${UTILROOT}/fakedbn
    export NWROOT=/gpfs/hps3/emc/global/noscrub/emc.glopara/svn/gfs/q3fy17_final
    export COMROOT=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/com
    export PCOMROOT=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/pcom
    export KEEPDATA=YES
    ;;
  eval)
    export envir=para
    export jlogfile=${jlogfile:-${COMROOT}/logs/${envir}/jlogfile}
    export DATAROOT=${DATAROOT:-/gpfs/hps2/nco/ops/tmpnwprd}
    if [ "$SENDDBN" == "YES" ]; then
       export DBNROOT=${UTILROOT}/para_dbn
       SENDDBN_NTC=NO
    else
       export DBNROOT=${UTILROOT}/fakedbn
    fi
    ;;
  para|test)
    export CRAY_F_SET=hps2 
    export EMCPEN=${EMCPEN:-%EMCPEN:ecfgfs2017%}
    export jlogfile=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/com/jlogfile
    export DATAROOT=${DATAROOT:-/gpfs/${CRAY_F_SET}/stmp/emc.glopara/%EMCPEN%}
    export DBNROOT=${UTILROOT}/fakedbn
    export NWROOT=/gpfs/hps3/emc/global/noscrub/emc.glopara/svn/gfs/q3fy17_final
    export COMROOT=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/com
    export COMOUT_ROOT=$COMROOT
    export PCOMROOT=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/pcom/prod
    export GESROOT=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/nwges
    export GESROOThps=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/nwges
    export GESROOTp1=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/nwges
    export GESROOTp2=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/nwges
    export KEEPDATA=YES
    ;;
  emcpara)
    export CRAY_F_SET=hps2
    export EMCPEN=${EMCPEN:-%EMCPEN:ecfgfs2017%}
    export jlogfile=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/com/jlogfile
    export DATAROOT=${DATAROOT:-/gpfs/hps3/stmp/emc.glopara/%EMCPEN%}
    export DBNROOT=${UTILROOT}/fakedbn
    export NWROOT=/gpfs/hps3/emc/global/noscrub/emc.glopara/svn/gfs/q3fy17_final
    export COMROOT=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/com
    export PCOMROOT=/gpfs/${CRAY_F_SET}/ptmp/emc.glopara/%EMCPEN%/pcom
    export KEEPDATA=YES
    ;;
  *)
    ecflow_client --abort="ENVIR must be prod, para, eval,emcpara , or test [envir.h]"
    exit
    ;;
esac

export SENDECF=${SENDECF:-YES}
export SENDCOM=${SENDCOM:-YES}
#### export KEEPDATA=YES

if [ -n "%PDY:%" ]; then 
  export PDY=${PDY:-%PDY:%}
  export RETRORUN="YES"
fi
if [ -n "%COMPATH:%" ]; then export COMPATH=${COMPATH:-%COMPATH:%}; fi
if [ -n "%MAILTO:%" ]; then export MAILTO=${MAILTO:-%MAILTO:%}; fi
if [ -n "%DBNLOG:%" ]; then export DBNLOG=${DBNLOG:-%DBNLOG:%}; fi
