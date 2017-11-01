#!/bin/bash

CHECKOUT_DIR=$PWD

CHECKOUT='TRUE'
#CHECKOUT='FALSE'
BUILD='TRUE'
#BUILD='FALSE'
CREATE_EXP='TRUE'
#CREATE_EXP='FALSE'
RUNROCOTO='TRUE'
#RUNROCOTO='FALSE'

regressionID='svntrunk'
idate='2017073118'
edate='2017080206'

ICS_dir_cray='/gpfs/hps3/emc/global/noscrub/emc.glopara/ICS'
PTMP_cray='/gpfs/hps3/ptmp'
ICS_dir_theia='/scratch4/NCEPDEV/global/noscrub/glopara/ICS/FV3GFS'
PTMP_theia='/scratch4/NCEPDEV/stmp4'

#fv3gfs_git_branch='master'
# Leave fv3gfs_svn_url blank to use git branch in fv3gfs_git_branch
fv3gfs_svn_url=' https://svnemc.ncep.noaa.gov/projects/fv3gfs/trunk'
load_rocoto='rocoto/1.2.4'

log_message () {
 logtime=`date`
 echo "LOG : $logtime : $1 : $2"
 if [[ $1 == "CRITICAL" ]]; then
  exit -1
 fi
}

if [ -d /scratch4/NCEPDEV ]; then
    system="theia"
elif [ -d /gpfs/hps3 ]; then
    system="cray"
else
    log_message "CRITICAL" "Unknown machine $system, not supported"
    exit -1
fi

module load $load_rocoto
rocotoruncmd=`which rocotorun`
if [[ -z ${rocotoruncmd} ]]; then
  log_message "CRITICAL" "module load for rocoto ($load_rocoto) on system failed"
fi

# system dependent
#----------------- 

if [[ $system != "cray" ]] && [[ $system != 'theia' ]]; then
 log_message "CRITICAL" "system setting: $system is not set correctly (only options are cray or theia)"
fi

if [[ $system == "cray" ]]; then
 ICS_dir=$ICS_dir_cray
 PTMP=$PTMP_cray
else
 ICS_dir=$PTMP_theia
 PTMP=$PTMP_theia
fi

comrot="$PTMP/$USER/fv3gfs_regression_tests"
if [[ -z $comrot ]]; then
  log_message "INFO" "createing directory $comrot"
  mkdir -p $comrot
  if [[ $? == 0 ]]; then
    log_message "CRITICAL" "comrot directory base directory did not exsist and could not be crated at: $comrot"
  fi
fi

rocotover=`$rocotoruncmd --version`
log_message "INFO" "using rocoto version $rocotover"
rocotostatcmd=`which rocotostat`

fv3gfs_ver='v15.0.0'
num_expected_exec='29'

pslot_basename='fv3gfs'
checkout_dir_basename="${pslot_basename}_sorc_${regressionID}"
pslot="${pslot_basename}_exp_${regressionID}"

username=`echo ${USER} | tr '[:upper:]' '[:lower:]'`
setup_expt=${CHECKOUT_DIR}/${checkout_dir_basename}/gfs_workflow.${fv3gfs_ver}/ush/setup_expt.py
setup_workflow=${CHECKOUT_DIR}/${checkout_dir_basename}/gfs_workflow.${fv3gfs_ver}/ush/setup_workflow.py
config_dir=${CHECKOUT_DIR}/${checkout_dir_basename}/gfs_workflow.${fv3gfs_ver}/config
comrot_test_dir=$comrot/$pslot

if [[ $CHECKOUT == 'TRUE' ]]; then
  cd ${CHECKOUT_DIR}
  if [[ ! -z ${fv3gfs_svn_url} ]]; then

    if [[ -d ${checkout_dir_basename} ]]; then
       rm -Rf ${checkout_dir_basename}
    fi
    log_message "INFO" "checking out fv3gfs from svn $fv3gfs_svn_url"
    svn co $fv3gfs_svn_url ${checkout_dir_basename}

  else

   log_message "INFO" "cloneing fvgfs from git with branch $fv3gfs_git_branch"
   #git clone http://${username}@vlab.ncep.noaa.gov/git/fv3gfs ${checkout_dir_basename}
   git clone ssh://${username}@vlab.ncep.noaa.gov:29418/fv3gfs ${checkout_dir_basename}

   if [[ ! -z "${fv3gfs_git_branch}// }" ]]; then
    cd ${checkout_dir_basename}
    git checkout remotes/origin/${fv3gfs_git_branch} -b ${fv3gfs_git_branch}
    cd ${CHECKOUT_DIR}
   fi

  fi
fi

exp_setup_string="--pslot ${pslot} --icsdir $ICS_dir --configdir ${config_dir} --comrot ${comrot} --idate $idate --edate $edate --expdir ${CHECKOUT_DIR}"
EXP_FULLPATH=${CHECKOUT_DIR}/${pslot}

if [[ $CREATE_EXP == 'TRUE' ]]; then

    log_message "INFO" "setting up experment: ${setup_expt} ${exp_setup_string}"
    removed=''
    if [[ -d $EXP_FULLPATH ]]; then
     removed='it was present but now has been removed'
    fi
    rm -Rf $EXP_FULLPATH
    log_message "INFO" "experment directory is $EXP_FULLPATH $removed"
    removed=''
    if [[ -d ${comrot}/${pslot} ]]; then
     removed='it was present but now has been removed'
    fi
    rm -Rf ${comrot}/${pslot}
    log_message "INFO" "comrot directory is $EXP_FULLPATH $removed"

    ${setup_expt} ${exp_setup_string}
    log_message "INFO" "setting up workflow: ${setup_workflow} --expdir $EXP_FULLPATH"
    ${setup_workflow} --expdir $EXP_FULLPATH

fi


if [[ $BUILD == 'TRUE' ]]; then
 cd ${checkout_dir_basename}/global_shared.${fv3gfs_ver}/sorc

   log_message "INFO" "running checkout script: $PWD/checkout.sh $username"
  ./checkout.sh $username
   log_message "INFO" "running build script: $PWD/build_all.sh $system"
  ./build_all.sh ${system}
  num_shared_exec=`ls -1 ../exec | wc -l`
 if [[ $num_shared_exec != $num_expected_exec ]]; then
   log_message "WARNING" "number of executables in shared exec: $num_shared_exec was found and was expecting $num_expected_exec"
   filepath='../exe'
   fullpath=`echo $(cd $(dirname $filepath ) ; pwd ) /$(basename $filepath )`
   log_message "WARNING" "check the executables found in: $fullpath"
 else
   log_message "INFO" "number of executables in shared exec: $num_shared_exec"
 fi
fi

if [[ ! -d ${EXP_FULLPATH} ]]; then
  log_message "CRITICAL" "experment directory $EXP_FULLPATH not found"
fi
cd ${EXP_FULLPATH}

if [[ $RUNROCOTO == 'TRUE' ]]; then
log_message "INFO" "Starting to run fv3gfs cycling regression test run using $rocotoruncmd -d ${pslot}.db -w ${pslot}.xml -v 10"

$rocotoruncmd -d ${pslot}.db -w ${pslot}.xml
if [[ $? != 0 ]]; then
  log_message "CRITICAL" "rocotorun failed on first attempt"
fi
if [[ -d ${pslot}.db ]]; then
 log_message "CRITICAL" "rocotorun failed to create database file"
fi
log_message "INFO" "rocotorun successfully ran initial rocoorun to to create database file:  ${pslot}.db"

log_message "INFO" "running: $rocotostatcmd -d ${pslot}.db -w ${pslot}.xml -s -c all | tail -1 | awk '{print $1}'"
lastcycle=`$rocotostatcmd -d ${pslot}.db -w ${pslot}.xml -s -c all | tail -1 | awk '{print $1}'`
if [[ $? != 0 ]]; then
 log_message "CRITICAL" "rocotostat failed when determining last cycle in test run"
fi
log_message "INFO" "rocotostat determined that the last cycle in test is: $lastcycle"

cycling_done="FALSE"
while [ $cycling_done == "FALSE" ]; do
  lastcycle_state=`$rocotostatcmd -d ${pslot}.db -w ${pslot}.xml -c $lastcycle -s | tail -1 | awk '{print $2}'`
  if [[ $lastcycle_state == "Done" ]]; then
   break
  fi
  log_message "INFO" "running: $rocotostatcmd -d ${pslot}.db -w ${pslot}.xml -c all"
  deadjobs=`$rocotostatcmd -d ${pslot}.db -w ${pslot}.xml -c all | awk '$4 == "DEAD" {print $2}'`
  if [[ ! -z $deadjobs ]]; then
     deadjobs=`echo $deadjobs | tr '\n' ' '`
     log_message "CRITICAL" "the following jobs are DEAD: $deadjobs"
  fi
  deadcycles=`$rocotostatcmd -d ${pslot}.db -w ${pslot}.xml -c $lastcycle -s | awk '$2 == "Dead" {print $1}'`
  if [[ ! -z $deadcycles ]]; then
   log_message "CRITICAL" "the following cycles are not dead: $deadcycles"
  fi
  $rocotoruncmd -d ${pslot}.db -w ${pslot}.xml
  if [[ $? == "0" ]]; then
   log_message "INFO" "Successfull: $rocotoruncmd -d ${pslot}.db -w ${pslot}.xml"
  else 
   log_message "WARNING" "FAILED: $rocotoruncmd -d ${pslot}.db -w ${pslot}.xml"
  fi
  sleep 5m
done

log_message "INFO" "Rocotorun completed successfully"

fi
