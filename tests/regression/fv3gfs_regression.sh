#!/bin/bash

usage () {
   echo -e "\033[1mUSAGE:\033[0m\n $0 [[baseline]] [[compair]] [[--non-interactive]]\n"
   echo -e "\tno arguments           : creates a baseline with sorc and exp dir in \$PWD named fvgfs_sorc_baseline fv3gfs_exp_basline respectivly"
   echo -e "\tone argument  (string) : creates a baseline with sorc and exp dir in \$PWD named fvgfs_sorc_\${string} fv3gfs_exp_\${string} respectivly\n\n"
   echo -e "\tone argument  (dir)       : creates a test run with sorc and exp dir in \$PWD named fvgfs_sorc_test_run   fv3gfs_exp_test_run respectivly \n\t\t\t\t    and then compairs the resluts against the comrot found in the directory \${dir}"
   echo -e "\ttwo arguments (dir) (str) : creates a test_run with sorc and exp dir in \$PWD named fvgfs_sorc_\${string} fv3gfs_exp_\${srting} respectivly \n\t\t\t\t    and then compairs the resluts against the comrot found in the directory \${dir} "
   echo -e "\ttwo arguments (dir) (dir) : does a bitwise compair on the gfs files from the first dir to the second\n"
   echo -e "\tthird optional argument is used when acctually running the script so no promps are given, otherwize the script will report on the settings.\n\n"
   echo -e "\033[1mEXAMPLE:\033[0m\n"
   echo -e "\tnohup ./fv3gfs_regression.sh fv3gfs_regression_baseline --non-interactive > & fv3gfs_regression_test_run.log &\n"
   exit
}


# Traps that only allow the above inputs

if [[ "$#" -gt "3" ]] || [[ $1 == '--help' ]]; then
 usage
fi

if [[ "$#" == "2" ]] || [[ "$#" == "3" ]]; then
 if [[ ! -d $1 ]] && [[ ! -d $2 ]]; then
  usage
 fi
fi

if [[ -f $1 ]] || [[ -f $2 ]]; then
 usage
fi

log_message () {
 logtime=`date`
 echo -e "LOG : $logtime : $1 : $2"
 if [[ $1 == "CRITICAL" ]]; then
  exit -1
  exit -1
 fi
}

CHECKOUT_DIR=$PWD

CHECKOUT='TRUE'
#CHECKOUT='FALSE'
BUILD='TRUE'
#BUILD='FALSE'
CREATE_EXP='TRUE'
#CREATE_EXP='FALSE'
RUNROCOTO='TRUE'
#RUNROCOTO='FALSE'

regressionID='baseline'
idate='2017073118'
edate='2017080106'

ICS_dir_cray='/gpfs/hps3/emc/global/noscrub/emc.glopara/ICS'
PTMP_cray='/gpfs/hps3/ptmp'
ICS_dir_theia='/scratch4/NCEPDEV/global/noscrub/glopara/ICS/FV3GFS'
PTMP_theia='/scratch4/NCEPDEV/stmp4'

find_data_dir () {

    local _check_baseline_dir=$1

    STARTTIME=$(date +%s)
    while IFS= read -r -d '' file
    do
       gfsfile=`basename $file | cut -f 1 -d"."`
       if [[ $gfsfile == "enkf" ]]; then
          check_real_base_dir=`dirname $file`
          if ls $check_real_base_dir/gdas.* 1> /dev/null 2>&1; then
           real_base_dir=$check_real_base_dir
           break 
          fi
       fi
       if [[ $(($ENDTIME - $STARTTIME)) > 20 ]]; then
         log_message "CRITICAL" "looking for valid baseline directory put then gave up after a minute"
       fi
    done < <(find $_check_baseline_dir -print0 )

    if [[ -z $real_base_dir ]]; then
      log_message "CRITICAL" "$_check_baseline_dir is not a directory with a baseline to test in it"
    fi
    #if [[ $real_base_dir != $_check_baseline_dir ]]; then
    #log_message "WARNING" "given directory did not have gfs data, but a subsiquent subdirectory was found that did"
    #fi
    _check_baseline_dir=`dirname $file`
    #log_message "INFO" "found baseline fv3gfs gfs data found in directory: $_check_baseline_dir"
    echo $_check_baseline_dir
}

COMPAIR_BASE='FALSE'
if [[ ! -d $1 ]] && [[ ! -f $1 ]]; then
 if [[ -z $1 || $1 == "--non-interactive" ]]; then
    regressionID='baseline'
    log_message "INFO" "No arguments given assuming to make new baseline with default ID: $regressionID"
 fi
fi

log_message "INFO" "running regression script on host $HOST"

checkout_dir_basename="${pslot_basename}_sorc_${regressionID}"
pslot="${pslot_basename}_exp_${regressionID}"

if [[ -d $1 ]]; then
  check_baseline_dir=`readlink -f $1`
  if [[ -z $2 ]] && [[ ! -d $2 ]] ; then
   regressionID='test_run'
  else
   if [[ $2 == "--non-interactive" ]]; then
     regressionID='test_run'
   else
     if [[ `echo $2  | cut -c1-2` == "--" ]]; then
       log_message "CRITICAL" "an errounous option was given ($2), --non-interactive is the only allowable option"
     else
       regressionID=$2
     fi
   fi
  fi
  pslot_basename='fv3gfs'
  checkout_dir_basename="${pslot_basename}_sorc_${regressionID}"
  pslot="${pslot_basename}_exp_${regressionID}"
  log_message "INFO" "running test run ($regressionID) agaist regression baseline in directory $check_baseline_dir"
  COMPAIR_BASE='TRUE'
fi

if [[ $COMPAIR_BASE == 'TRUE' ]]; then
 check_baseline_dir_get=$( find_data_dir $check_baseline_dir )
 if [[ $check_baseline_dir != $check_baseline_dir_get ]]; then
    check_baseline_dir=$check_baseline_dir_get
    log_message "WARNING" "given directory did not have gfs data, but a subsiquent subdirectory was found that did"
    log_message "INFO" "found baseline fv3gfs gfs data found in directory: $check_baseline_dir"
 fi
fi

fv3gfs_git_branch='master'
# Leave fv3gfs_svn_url blank to use git branch in fv3gfs_git_branch
fv3gfs_svn_url=''
load_rocoto='rocoto/1.2.4'

if [[ -d /scratch4/NCEPDEV ]]; then
  system="theia"
elif [[ -d /gpfs/hps3 ]]; then
  system="cray"
else
  log_message "CRITICAL" "Unknown machine $system, not supported"
  exit -1
fi

JUST_COMPAIR_TWO_DIRS='FALSE'
if [[ -d $1 ]] && [[ -d $2 ]]; then
 CHECKOUT='FALSE'
 BUILD='FALSE'
 CREATE_EXP='FALSE'
 RUNROCOTO='FALSE'
 check_baseline_dir_with_this_dir=`readlink -f $2`
 check_baseline_dir_with_this_dir=$( find_data_dir $check_baseline_dir_with_this_dir )
 log_message "INFO" "Simply doing a diff on these two directories:\n  $check_baseline_dir \n  $check_baseline_dir_with_this_dir"
 JUST_COMPAIR_TWO_DIRS='TRUE'
fi

INTERACTIVE='TRUE'
if [[ $1 == "--non-interactive" ]] || [[ $2 == "--non-interactive" ]] || [[ $3 == "--non-interactive" ]]; then
   INTERACTIVE='FALSE'
fi


if [[ $INTERACTIVE == "TRUE" ]]; then
   echo -e "Current Settings are:\n"
   echo "regressionID = $regressionID"
   echo "idate        = $idate"
   echo "edate        = $edate"
   echo "CHECKOUT_DIR = $CHECKOUT_DIR"
   echo "CHECKOUT     = $CHECKOUT"
   echo "BUILD        = $BUILD"
   echo "CREATE_EXP   = $CREATE_EXP"
   echo "COMPAIR_BASE = $COMPAIR_BASE"
   echo -e "RUNROCOTO    = $RUNROCOTO\n"
   while read -n1 -r -p "Are these the correct settings (y/n): " answer
    do
    if [[ $answer == "n" ]]; then
     echo -e "\n"
     exit
    fi 
    if [[ $answer == "y" ]]; then
     break 
    fi
    echo ""
   done
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
 ICS_dir=$ICS_dir_theia
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

   log_message "INFO" "cloning fvgfs from git with branch $fv3gfs_git_branch"
   log_message "INFO" "git clone ssh://${username}@vlab.ncep.noaa.gov:29418/fv3gfs ${checkout_dir_basename}"
   git clone ssh://${username}@vlab.ncep.noaa.gov:29418/fv3gfs ${checkout_dir_basename}

   if [[ ! -z "${fv3gfs_git_branch}// }" ]]; then
    cd ${checkout_dir_basename}
    git checkout remotes/origin/${fv3gfs_git_branch} -b ${fv3gfs_git_branch}
    git rev-parse HEAD | xargs git show --stat
    cd ${CHECKOUT_DIR}
   fi

  fi
fi

exp_setup_string="--pslot ${pslot} --icsdir $ICS_dir --configdir ${config_dir} --comrot ${comrot} --idate $idate --edate $edate --expdir ${CHECKOUT_DIR}"
EXP_FULLPATH=${CHECKOUT_DIR}/${pslot}

if [[ $CREATE_EXP == 'TRUE' ]]; then

    log_message "INFO" "setting up experiment: ${setup_expt} ${exp_setup_string}"
    removed=''
    if [[ -d $EXP_FULLPATH ]]; then
     removed='it was present but now has been removed'
    fi
    rm -Rf $EXP_FULLPATH
    log_message "INFO" "experiment directory is $EXP_FULLPATH $removed"
    removed=''
    if [[ -d ${comrot}/${pslot} ]]; then
     removed='it was present but now has been removed'
    fi
    rm -Rf ${comrot}/${pslot}
    log_message "INFO" "comrot directory is ${comrot}/${pslot} $removed"

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

if [[ $RUNROCOTO == 'TRUE' ]]; then
    if [[ ! -d ${EXP_FULLPATH} ]]; then
     log_message "CRITICAL" "experiment directory $EXP_FULLPATH not found"
    fi
    log_message "INFO" "running regression script on host $HOST"
    log_message "INTO" "moving to PWD $EXP_FULLPATH to run cycleing in experiment directory"
    cd ${EXP_FULLPATH}

    log_message "INFO" "Starting to run fv3gfs cycling regression test run using $rocotoruncmd -d ${pslot}.db -w ${pslot}.xml"
    log_message "INFO" "running $rocotoruncmd from $PWD"

    $rocotoruncmd -d ${pslot}.db -w ${pslot}.xml
    if [[ $? != 0 ]]; then
      log_message "CRITICAL" "rocotorun failed on first attempt"
    fi
    if [[ -d ${pslot}.db ]]; then
     log_message "CRITICAL" "rocotorun failed to create database file"
    fi
    log_message "INFO" "rocotorun successfully ran initial rocoorun to to create database file:  ${pslot}.db"

    log_message "INFO" "running: $rocotostatcmd -d ${pslot}.db -w ${pslot}.xml -s -c all | tail -1 | awk '{print \$1}'"
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
       log_message "INFO" "Successful: $rocotoruncmd -d ${pslot}.db -w ${pslot}.xml"
      else 
       log_message "WARNING" "FAILED: $rocotoruncmd -d ${pslot}.db -w ${pslot}.xml"
      fi
      sleep 5m
    done

    log_message "INFO" "Rocotorun completed successfully"

fi

diff_file_name="${CHECKOUT_DIR}/diff_file_list_${regressionID}.txt"
if [[ $COMPAIR_BASE == 'TRUE' ]]; then
   if [[ $JUST_COMPAIR_TWO_DIRS=='TRUE' ]]; then
    comrot_test_dir=$check_baseline_dir_with_this_dir
   fi
   log_message "INFO" "doing the diff compair in $check_baseline_dir against $comrot_test_dir"
   if [[ ! -d $check_baseline_dir ]] || [[ ! -d $comrot_test_dir ]]; then
     log_message "CRITICAL" "One of the target directories does not exist"
   fi
   log_message "INFO" "Moving to direcotry $comrot to do the compare"
   if [[ -d $comrot ]]; then
     cd $comrot
   else
     log_message "CRITICAL" "The directory $comrot does not exsist"
   fi
   check_baseline_dir_basename=`basename $check_baseline_dir`
   comrot_test_dir_basename=`basename $comrot_test_dir`
   log_message "INFO" "running command: diff --brief -Nr --exclude \"*.log*\"  $check_baseline_dir_basename $comrot_test_dir_basename >& $$diff_file_name" 
   diff --brief -Nr --exclude "*.log*" $check_baseline_dir_basename $comrot_test_dir_basename >  ${diff_file_name} 2>&1
   log_message "INFO" "completed runing diff for fv3gfs regression test ($regressionID) resluts in file: $diff_file_name"
fi
