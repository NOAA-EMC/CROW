#!/bin/env bash

export REGRESSSION_ROTDIR_BASENAME='fv3gfs_regression_ROTDIRS'

usage () {
   echo -e "\033[1mUSAGE:\033[0m\n\t$0 [[baseline]] [[compare]] [[--non-interactive]]\n"
   echo -e "\tno arguments              : creates a baseline with sorc and exp dir in \$PWD named fvgfs_sorc_baseline fv3gfs_exp_basline respectivly"
   echo -e "\tone argument  (str)       : creates a baseline with sorc and exp dir in \$PWD named fvgfs_sorc_\${str} fv3gfs_exp_\${str} respectivly\n\n"
   echo -e "\tone argument  (dir)       : creates a test run with sorc and exp dir in \$PWD named fvgfs_sorc_test_run   fv3gfs_exp_test_run respectivly \n\t\t\t\t    and then compares the results against the comrot found in the directory \${dir}"
   echo -e "\ttwo arguments (dir) (str) : creates a test run with sorc and exp dir in \$PWD named fvgfs_sorc_\${str} fv3gfs_exp_\${srting} respectivly \n\t\t\t\t    and then compares the results against the comrot found in the directory \${dir} "
   echo -e "\ttwo arguments (dir) (dir) : does a bitwise compare on the gfs files from the first dir to the second\n"
   echo -e "\tthird optional argument is used when acctually running the script so no promps are given, otherwize the script will report on the settings.\n"
   echo -e "\033[1mEXAMPLE:\033[0m\n\tnohup ./fv3gfs_regression.sh baseline --non-interactive > & fv3gfs_regression_baseline_run.log &\n"
   echo -e "\033[1mNOTE:\033[0m\n\tCurret supported CASES: slurm (uses module load slurm and thus creates slurm ready XML)\n"
   exit
}

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
       if [[ $(($ENDTIME - $STARTTIME)) > 65 ]]; then
         log_message "CRITICAL" "looking for valid baseline directory put then gave up after a minute"
         exit -1
       fi
    ENDTIME=$(date +%s)
    done < <(find $_check_baseline_dir -print0 )

    if [[ -z $real_base_dir ]]; then
      exit -1
    fi
    _check_baseline_dir=`dirname $file`
    echo $_check_baseline_dir
}

INTERACTIVE='TRUE'
for arg
 do
  if [[ $arg == "--non-interactive" ]]; then
   INTERACTIVE='FALSE'
   break
  fi
done

# Traps that only allow the above inputs specified in the usage

if [[ "$#" -gt "4" ]] || [[ $1 == '--help' ]]; then
 usage
fi

if [[ "$#" -ge "3" ]]; then  
 if [[ ! -d $1 ]]; then
  usage
 fi
fi

if [[ -f $1 ]] || [[ -f $2 ]]; then
 usage
fi

log_message () {
 logtime=`date +"%F %T"`
 echo -e "$1 : bash : $logtime : LOG : $2"
 if [[ $1 == "CRITICAL" ]]; then
  exit -1
 fi
}

CHECKOUT_DIR=$PWD
ROCOTO_WAIT_FRQUANCY='5m'

CHECKOUT=${CHECKOUT:-'TRUE'}
CREATE_EXP=${CREATE_EXP:-'TRUE'}
BUILD=${BUILD:-'TRUE'}
CREATE_EXP=${CREATE_EXP:-'TRUE'}
RUNROCOTO=${RUNROCOTO:-'TRUE'}
JOB_LEVEL_CHECK=${JOB_LEVEL_CHECK:-'FALSE'}
#RZDM_RESULTS=${RZDM_RESULTS:-'FALSE'}
PYTHON_FILE_COMPARE=${PYTHON_FILE_COMPARE:-'TRUE'}

#CHECKOUT='FALSE'
#CREATE_EXP='FALSE'
#BUILD='FALSE'
#RUNROCOTO='FALSE'
#JOB_LEVEL_CHECK='TRUE'
#RZDM_RESULTS='TRUE'
#PYTHON_FILE_COMPARE='FALSE'

fv3gfs_git_branch='slurm_beta'

module use /scratch4/NCEPDEV/global/save/Terry.McGuinness/git/Rocoto-fix-terry-3/modulefile
load_rocoto='fix-terry-3_local'

ICS_dir_cray='/gpfs/hps3/emc/global/noscrub/emc.glopara/CROW/ICS'
PTMP_cray='/gpfs/hps3/ptmp'
ICS_dir_theia='None'
PTMP_theia='/scratch4/NCEPDEV/stmp4'

# system dependent
#----------------- 
if [[ -d /scratch4/NCEPDEV ]]; then
  system="theia"
#elif [[ -d /gpfs/hps3 ]]; then
#  system="wcoss_cray"
else
  log_message "CRITICAL" "Unknown machine $system, not supported"
fi

# TODO prepare for JET, Gaea
if [[ $system == "wcoss_cray" ]]; then
 ICS_dir=$ICS_dir_cray
 PTMP=$PTMP_cray
else
 ICS_dir=$ICS_dir_theia
 PTMP=$PTMP_theia
fi

module unload intelpython
python_check=$(which python)
if [[ -z ${python_check} ]]; then
   log_message "CRITICAL" "python two shoule be in /usr/bin/python and was not found (check your path)"
fi
python_version=$($python_check --version 2>&1)
log_message "INFO" "using python two from $python_check $python_version"

if [[ $PYTHON_FILE_COMPARE == "TRUE" ]]; then
   execPATH="`dirname \"$0\"`"
   execPATH="`( cd \"$execPATH\" && pwd )`"
   if [ -z "$execPATH" ] ; then
    log_message "CRITICAL" "can not access locate $execPATH where this script was lauched"
   fi
  
   COMPARE_FOLDERS=$execPATH/compare_GFS_comdirs.py
   if [[ ! -f $COMPARE_FOLDERS ]]; then
     log_message "CRITICAL" "the python script compare_GFS_comdirs.py could not be located\nit should be located in the same directory where the regression script is lauched $execPATH"
   fi
  
   if [[ $system == "theia" ]]; then
    module use /scratch4/NCEPDEV/nems/noscrub/emc.nemspara/python/modulefiles
    module load python/3.6.1-emc
   else
    log_message "CRITICAL" "this script needs to be ported to the non-Thiea systems"
   fi
fi
  
python_check=$(which python3)
if [[ -z ${python_check} ]]; then
   log_message "CRITICAL" "python three shoule be in your path from ../NCEPDEV/nems/noscrub/emc.nemspara/python/modulefiles via module load python/3.6.1-emc\nbut module failed to load"
fi
python_version=$($python_check --version 2>&1)
log_message "INFO" "using python three from $python_check $python_version"

module load $load_rocoto
rocotoruncmd=$(which rocotorun)
if [[ -z ${rocotoruncmd} ]]; then
  log_message "CRITICAL" "module load for rocoto ($load_rocoto) on system failed"
fi
 
rocotover=$($rocotoruncmd --version)
log_message "INFO" "rocotorun found here: $rocotoruncmd"
log_message "INFO" "using rocoto version $rocotover"
rocotostatcmd=$(which rocotostat)
if [[ -z ${rocotostatcmd} ]]; then
  log_message "CRITICAL" "($rocotostatcmd) not found on system"
fi

#fv3gfs_ver='v15.0.0'
num_expected_exec='51'

if [[ ! -d $1 ]] && [[ ! -f $1 ]]; then
 if [[ -z $1 || $1 == "--non-interactive" ]]; then
    regressionID='baseline'
    log_message "INFO" "No arguments given assuming to make new baseline with default ID: $regressionID"
 else 
    regressionID=$1
    log_message "INFO" "only the baseline will be created with ID: $regressionID"
 fi
fi


#=======================================
# CASE = global-slurm-test
# ./setup_expt.py --pslot gw_C384C192_2019021400_IC --comrot /scratch4/NCEPDEV/global/noscrub/Terry.McGuinness/ROTDIRS --expdir /scratch4/NCEPDEV/global/noscrub/Terry.McGuinness/expdir --idate 2019021400 --edate 2019021412 --configdir /scratch4/NCEPDEV/global/save/Terry.McGuinness/git/global-workflow/parm/config --resdet 384 --resens 192 --nens 80 --gfs_cyc 4

#======================================
# CASE defualt
# $HOMEgfs/setup_expt.py --pslot $yourPSLOT --resdet 384 --resens 192 --comrot $yourROTDIRS --expdir $yourEXPDIR --idate 2017073118 --edate 2017080100 --icsdir /scratch4/NCEPDEV/da/noscrub/Catherine.Thomas/ICSDIR --configdir $HOMEgfs/parm/config --nens 24 --cdump gdas --gfs_cyc 1


# If RZDM is set then the viewer will attempt to post the state of the workflow in html on the rzdm server
#RZDM='tmcguinness@emcrzdm.ncep.noaa.gov:/home/www/emc/htdocs/gc_wmb/tmcguinness'
#ROCOTOVIEWER='/u/Terry.McGuinness/bin/rocoto_viewer.py'

log_message "INFO" "running regression script on host $HOST with PID $BASHPID"

COMPARE_BASE='FALSE'
JUST_COMPARE_TWO_DIRS='FALSE'

if [[ -d $1 ]] && [[ -d $2 ]]; then
 CHECKOUT='FALSE'
 BUILD='FALSE'
 CREATE_EXP='FALSE'
 RUNROCOTO='FALSE'

 check_baseline_dir_with_this_dir=`readlink -f $2`
 check_baseline_dir=`readlink -f $1`

 #TODO this needs to be simplified and refactored
 #check_baseline_dir_get=$( find_data_dir $check_baseline_dir )
 check_baseline_dir_get=$check_baseline_dir

 if [[ -z $check_baseline_dir_get ]]; then
   log_message "CRITICAL" "$check_baseline_dir_get is not a directory with a baseline to test in it"
 fi
 if [[ $check_baseline_dir != $check_baseline_dir_get ]]; then
   check_baseline_dir=$check_baseline_dir_get
   log_message "WARNING" "given directory did not have gfs data, but a subsequent subdirectory was found that did:\n$check_baseline_dir"
 fi  

 #TODO this needs to be simplified and refactored
 #check_baseline_dir_with_this_dir_get=$( find_data_dir $check_baseline_dir_with_this_dir )
 check_baseline_dir_with_this_dir_get=$check_baseline_dir_with_this_dir

 if [[ -z $check_baseline_dir_with_this_dir_get ]]; then
   log_message "CRITICAL" "$check_baseline_dir_with_this_get is not a directory with a baseline to test in it"
 fi
 if [[ $check_baseline_dir_with_this_dir_get != $check_baseline_dir_with_this_dir ]]; then
   check_baseline_dir_with_this_dir=$check_baseline_dir_with_this_get
   log_message "WARNING" "given directory did not have gfs data, but a subsequent subdirectory was found that did:\n$check_baseline_dir_with_this_dir"
 fi  
 log_message "INFO" "simply doing a diff on these two directories:\n  $check_baseline_dir \n  $check_baseline_dir_with_this_dir"
 JUST_COMPARE_TWO_DIRS='TRUE'
 COMPARE_BASE='TRUE'
 if [[ -z $3 ]]; then
   regressionID='compare'
 else
   if [[ $3 != "--non-interactive" ]]; then
     regressionID=$3
   else
     regressionID='compare'
   fi
 fi
elif [[ -d $1 && ! -d $2 ]]; then
  check_baseline_dir=`readlink -f $1`
  if [[ -z $2 ]]; then
   :
   #regressionID='test_run'
  else
   if [[ $2 == "--non-interactive" ]]; then
     :
     #regressionID='test_run'
   else
     if [[ `echo $2  | cut -c1-2` == "--" ]]; then
       log_message "CRITICAL" "an errounous option was given ($2), --non-interactive is the only allowable option"
     else
       regressionID=$2
     fi
   fi
  fi
  log_message "INFO" "running test run ($regressionID) agaist regression baseline in directory $check_baseline_dir"
  COMPARE_BASE='TRUE'
  #TODO need to refactor check_baseline_dir_get : multiple arg logic tricky and hard to support
  #check_baseline_dir_get=$( find_data_dir $check_baseline_dir )
  check_baseline_dir_get=$check_baseline_dir
  if [[ -z $check_baseline_dir_get ]]; then
   log_message "CRITICAL" "$check_baseline_dir_get is not a directory with a baseline to test in it"
  fi
  if [[ $check_baseline_dir != $check_baseline_dir_get ]]; then
    check_baseline_dir=$check_baseline_dir_get
    log_message "WARNING" "given directory did not have gfs data, but a subsequent subdirectory was found that did:\n$check_baseline_dir"
  fi
 log_message "INFO" "found baseline fv3gfs gfs data found in directory: $check_baseline_dir"
fi

#if [[ -z $ROCOTOVIEWER ]]; then
#  RZDM_RESULTS="FALSE"
#fi


# Check to see if user entered a CASE from regressionID
CASE=$regressionID
special_case_found="FALSE"
fv3gfs_git_branch='slurm_beta'
ICS_dir="/scratch4/NCEPDEV/da/noscrub/Catherine.Thomas/ICSDIR"
if [[ ! -d "$ICS_dir" ]]; then
   log_message "CRITICAL" "Using base case but ICSDIR directory does not exsist: $ICS_dir"
fi
log_message "INFO" "Using ICSDIR from Cathy as default base case"
log_message "INFO" "ICSDIR: $ICS_dir"

if [[ $CASE == "slurm" ]]; then
  log_message "INFO" "using special CASE slurm so using branch beta_slurm"
  log_message "INFO" "using slurm so loading slurm module for running test case"
  module load slurm
  special_case_found="TRUE"
  fv3gfs_git_branch='slurm_beta'
elif [[ $CASE == "master" ]]; then
  log_message "INFO" "using spcial case (master) so global-worfflow will be cloning from master"
  special_case_found="TRUE"
  fv3gfs_git_branch='master'
  module unload slurm
  log_message "INFO" "using spcial case (master) so module unload slurm was issued"
elif [[ $CASE == "baseline" ]]; then
  log_message "INFO" "using spcial case (baseline) so module unload slrum is issued"
  special_case_found="TRUE"
  module unload slurm
fi

regressionID=${regressionID:-'test_run'}
pslot_basename='fv3gfs'
checkout_dir_basename="${pslot_basename}_sorc_${regressionID}"
pslot="${pslot_basename}_exp_${regressionID}"
setup_expt=${CHECKOUT_DIR}/${checkout_dir_basename}/ush/rocoto/setup_expt.py

log_message "INFO" "Running default case with regressionID: $regressionID" 
setup_workflow=${CHECKOUT_DIR}/${checkout_dir_basename}/ush/rocoto/setup_workflow.py
config_dir=${CHECKOUT_DIR}/${checkout_dir_basename}/parm/config

username=`echo ${USER} | tr '[:upper:]' '[:lower:]'`

comrot=${CHECKOUT_DIR}/${REGRESSSION_ROTDIR_BASENAME}
comrot_test_dir=${comrot}/${pslot}
exp_dir_fullpath=${CHECKOUT_DIR}/${pslot}

#TODO Stop HERE and make sure default values for baseline canned case are present

link_args='emc theia'

idate='2017073118'
edate='2017080106'

EXTRA_SETUP_STRING="--resdet 384 --resens 192 --nens 24 --gfs_cyc 1"
COPY_WARM_ICS=${COPY_WARM_ICS:-'FALSE'}


if [[ $ICS_dir == "None" ]]; then
   exp_setup_string="--pslot ${pslot} --configdir ${config_dir} --comrot ${comrot} --idate $idate --edate $edate --expdir ${CHECKOUT_DIR} $EXTRA_SETUP_STRING"
else
   exp_setup_string="--pslot ${pslot} --icsdir $ICS_dir --configdir ${config_dir} --comrot ${comrot} --idate $idate --edate $edate --expdir ${CHECKOUT_DIR} $EXTRA_SETUP_STRING"
fi

echo -e "\nScript Control Settings (env vars)"
echo -e "===================================="

echo "CHECKOUT      = $CHECKOUT"
echo "BUILD         = $BUILD"
echo "CREATE_EXP    = $CREATE_EXP"
echo "RUNROCOTO     = $RUNROCOTO"
echo "COMPARE_BASE  = $COMPARE_BASE"
echo "COPY_WARM_ICS = $COPY_WARM_ICS"

echo -e "\nRepo and filepaths Settings"
echo -e "============================"
echo "regressionID = $regressionID"
echo "git branch   = $fv3gfs_git_branch"
echo "CHECKOUT_DIR = $CHECKOUT_DIR"
echo "link args    = $link_args"
#echo "RZDM_RESULTS = $RZDM_RESULTS"
echo "PYTHON_FILE_COMPARE = $PYTHON_FILE_COMPARE"
echo -e "JOB_LEVEL_CHECK = $JOB_LEVEL_CHECK"
if [[ $special_case_found == "TRUE" ]]; then
echo "Special CASE = $CASE"
fi

echo -e "\nModel Workflow Configuration Settings"
echo "======================================"
echo "IDATE  : $idate"
echo "EDATE  : $edate"
echo "PSLOT  : $pslot"
echo "ROTDIR : $comrot"
echo "CONFIG : $config_dir"
echo "ICDIR  : $ICS_dir"
echo "IDATE  : $idate"
echo "EDATE  : $edate"
echo "EXPDIR : $exp_dir_fullpath"
echo -e "EXTRA  : $EXTRA_SETUP_STRING\n"

if [[ $INTERACTIVE == "TRUE" ]]; then
  echo -e "To run with these settings append --non-interactive for the final argument and re-run this script\n\n"
  exit 0
fi

#if [ $INTERACTIVE == "TRUE" ] || [ $- == *i* ]; then
#   while read -n1 -r -p "Are these the correct settings (y/n): " answer
#    do
#    if [[ $answer == "n" ]]; then
#     echo -e "\n"
#     exit
#    fi 
#    if [[ $answer == "y" ]]; then
#     echo -e "\n"
#     break 
#    fi
#    echo ""
#   done
#fi

SCRIPT_STARTTIME=$(date +%s)

if [[ $CHECKOUT == 'TRUE' ]]; then
  cd ${CHECKOUT_DIR}
  
  fv3gfs_repo_name='global-workflow'
  log_message "INFO" "git clone ssh://${username}@vlab.ncep.noaa.gov:29418/$fv3gfs_repo_name ${checkout_dir_basename}"
  git clone ssh://${username}@vlab.ncep.noaa.gov:29418/$fv3gfs_repo_name ${checkout_dir_basename}

  if [[ ${fv3gfs_git_branch} != "master" ]]; then
   log_message "INFO" "git is now checkingout branch $fv3gfs_git_branch"
   cd ${checkout_dir_basename}
   git checkout remotes/origin/${fv3gfs_git_branch} -b ${fv3gfs_git_branch}
   git rev-parse HEAD | xargs git show --stat
   cd ${CHECKOUT_DIR}
  else
   log_message "INFO" "git clone left in master branch and no checkout was performed"
  fi
fi  

if [[ $BUILD == 'TRUE' ]]; then

   cd ${checkout_dir_basename}/sorc

   # This is in BUILD branch for you
   #sed -i  's/cd gsi.fd/cd gsi.fd\n    checkout DA-FV3-IMPL/' checkout.sh
   #log_message "WARNING" "just updated checkout.sh script and added line to checkout DA-FV3-IMPL branch for gsi instead of master"

   log_message "INFO" "running checkout script: $PWD/checkout.sh $username"
   export GIT_TERMINAL_PROMPT=0
  ./checkout.sh
   if [[ $? -ne 0 ]]; then
      log_message "CRITICAL" "checkout.sh script failed"
   fi
   log_message "INFO" "running build script: $PWD/build_all.sh $build_all_args"
  ./build_all.sh
   if [[ $? -ne 0 ]]; then
      log_message "CRITICAL" "build_all.sh script failed"
   fi
   log_message "INFO" "running link_fv3gfs.sh $link_args"
  ./link_fv3gfs.sh $link_args
   if [[ $? -ne 0 ]]; then
      log_message "CRITICAL" "link_fv3gfs.sh $link_args script failed"
   fi
  num_shared_exec=`ls -1 ../exec | wc -l`
  if [[ $num_shared_exec != $num_expected_exec ]]; then
    log_message "WARNING" "number of executables in shared exec: $num_shared_exec was found and was expecting $num_expected_exec"
    filepath='../exe'
    fullpath=`echo $(cd $(dirname $filepath ) ; pwd ) /$(basename $filepath )`
    log_message "WARNING" "check the executables found in: $fullpath"
  else
   log_message "INFO" "number of executables in shared exec found as expected: $num_shared_exec"
 fi
fi


if [[ $CREATE_EXP == 'TRUE' ]]; then

    log_message "INFO" "setting up experiment: ${setup_expt} ${exp_setup_string}"
    removed=''
    if [[ -d $exp_dir_fullpath ]]; then
     exp_dir_fullpath_movename=$exp_dir_fullpath.$(date +%H%M%S)
     mv $exp_dir_fullpath $exp_dir_fullpath_movename
     removed="but it was present so the prior directory was moved to $exp_dir_fullpath_movename"
    fi
    rm -Rf $exp_dir_fullpath
    log_message "INFO" "experiment directory is $exp_dir_fullpath $removed"
    removed=''
    if [[ -d $comrot_test_dir ]]; then
     comrot_test_dir_movename=$comrot_test_dir.$(date +%H%M%S)
     mv $comrot_test_dir $comrot_test_dir_movename
     removed="but it was present so the prior directory was moved to $comrot_test_dir_movename"
    fi
    rm -Rf $comrot_test_dir
    log_message "INFO" "comrot directory is $comrot_test_dir $removed"

    yes | ${setup_expt} ${exp_setup_string}
    log_message "INFO" "setting up workflow: ${setup_workflow} --expdir $exp_dir_fullpath"

    # Using Cathy T.'s case as defalut always when creating exp
    log_message "INTO" "Applying canned case configuration for exerment \'baseline\' which differs slightly from master branch"
    sed -i 's/USE_RADSTAT=\"NO\"/USE_RADSTAT=\"YES\"  # USE_RADSTAT set to YES by fv3gfs_regression.sh script/' $exp_dir_fullpath/config.eobs

    sed -i '/npe_gsi=$npe_anal/ i export USE_RADSTAT=\"YES\" # added by fv3gfs_regression.sh' $exp_dir_fullpath/config.anal
    log_message "INFO" "updated config.eobs and config.anal with USE_RADSTAT=YES"

    sed -i 's/export l4densvar=\".true.\"/export l4densvar=\".false.\"   #  l4densvar updated to be set to false by fv3gfs_regression.sh script/' $exp_dir_fullpath/config.base
    log_message "INFO" "updated config.base to have the  l4densvar=\".false.\""


    yes | ${setup_workflow} --expdir $exp_dir_fullpath

    if [[ -d $exp_dir_fullpath ]]; then
       log_message "INFO" "the experiment directory is present: $exp_dir_fullpath"
    else
       log_message "CRITICAL" "The experment directory was not created correctly"
    fi

fi


if [[ $COPY_WARM_ICS == "TRUE" ]]; then
  warm_start_files='/scratch3/NCEPDEV/stmp1/Kate.Friedman/FV3GFS_ICS/2019021400'
  log_message "INFO" "moving FV3GFS warmstart files for 2019021400 from: $warm_start_files"
  mkdir -p $comrot_test_dir/enkfgdas.20190214
  mkdir -p $comrot_test_dir/gdas.20190214
  rsync -rlptgoDv $warm_start_files/enkfgdas.20190214/ $comrot_test_dir/enkfgdas.20190214
  rsync -rlptgoDv $warm_start_files/gdas.20190214/ $comrot_test_dir/gdas.20190214
  log_message "INFO" "finished setting up warmstart files for 2019021400"
fi


run_file_compare_python () {

   total_number_files=`find $check_baseline_dir -type f | wc -l`
   if [[ $JUST_COMPARE_TWO_DIRS == 'TRUE' ]]; then
    comrot_test_dir=$check_baseline_dir_with_this_dir
   fi
   log_message "INFO" "doing the diff compare in $check_baseline_dir against $comrot_test_dir"
   if [[ ! -d $check_baseline_dir ]] || [[ ! -d $comrot_test_dir ]]; then
     log_message "CRITICAL" "one of the target directories does not exist"
   fi

   log_message "INFO" "loading module nccmp"
   module load nccmp
   log_message "INFO" "processing at lease $total_number_files using comprehensive pyton global file comparitor" 
   log_message "INFO" "running: compare_GFS_comdirs.py --ctotal_number_filesmp_dirs $check_baseline_dir $comrot_test_dir"
   $COMPARE_FOLDERS --cmp_dirs $check_baseline_dir $comrot_test_dir

}

run_file_compare () {

    log_message "INFO" "doing job level comparing with job $regressionID" 
    if [[ $COMPARE_BASE == 'TRUE' ]]; then
       PWD_start=$PWD
       diff_file_name="${CHECKOUT_DIR}/diff_file_list_${regressionID}.lst"
       total_number_files=`find $check_baseline_dir -type f | wc -l`
       if [[ $system == "theia" ]]; then
        module load nccmp
        NCCMP=`which nccmp`
       else
        NCCMP=/gpfs/hps3/emc/nems/noscrub/emc.nemspara/FV3GFS_V0_RELEASE/util/nccmp
       fi

       if [[ $JUST_COMPARE_TWO_DIRS == 'TRUE' ]]; then
        comrot_test_dir=$check_baseline_dir_with_this_dir
       fi
       log_message "INFO" "doing the diff compare in $check_baseline_dir against $comrot_test_dir"
       if [[ ! -d $check_baseline_dir ]] || [[ ! -d $comrot_test_dir ]]; then
         log_message "CRITICAL" "one of the target directories does not exist"
       fi
       log_message "INFO" "moving to directory $comrot_test_dir to do the compare"
       if [[ -d $comrot_test_dir ]]; then
         cd $comrot_test_dir/..
       else
         log_message "CRITICAL" "The directory $comrot_test_dir does not exsist"
       fi
       check_baseline_dir_basename=`basename $check_baseline_dir`
       comrot_test_dir_basename=`basename $comrot_test_dir`

       log_message "INFO" "running command: diff --brief -Nr --exclude \"*.log*\" --exclude \"*.nc\" --exclude \"*.nc?\"  $check_baseline_dir_basename $comrot_test_dir_basename >& $diff_file_name" 
       diff --brief -Nr --exclude "*.log*" --exclude "*.nc" --exclude "*.nc?" $check_baseline_dir_basename $comrot_test_dir_basename >> ${diff_file_name} 2>&1

       num_different_files=`wc -l < $diff_file_name`
       log_message "INFO" "checking of the $num_different_files differing files (not including NetCDF) for which ones are tar and/or compressed files for differences"
       rm -f ${diff_file_name}_diff
       counter_diffed=0
       counter_regularfiles=0
       counter_compressed=0
       while read line; do
        set -- $line;
        file1=$2;
        file2=$4;

           if ( tar --exclude '*' -ztf $file1 ) ; then
            #log_message "INFO" "$file1 is an compressed tar file"
            counter_compressed=$((counter_compressed+1))
            if [[ $( tar -xzf $file1 -O | md5sum ) != $( tar -xzf $file2 -O | md5sum ) ]] ; then
               #log_message "INFO" "found $file1 and $file2 gzipped tar files DO differ" 
               counter_diffed=$((counter_diffed+1))
               echo "compressed tar $line" >> ${diff_file_name}_diff
            fi
           elif ( tar --exclude '*' -tf  $file1 ) ; then
             counter_compressed=$((counter_compressed+1))
             #log_message "INFO" "$file1 is an uncompressed tar file"
             if [[ $( tar -xf $file1 -O | md5sum ) != $( tar -xf $file2 -O | md5sum ) ]] ; then
               #log_message "INFO" "found $file1 and $file2 tar files DO differ" 
               counter_diffed=$((counter_diffed+1))
               echo "tar $line" >> ${diff_file_name}_diff
             fi
           else
             #log_message "INFO" "$file1 is not tar or tar.gz and still then differs" 
             counter_regularfiles=$((counter_regularfiles+1))
             echo $line >> ${diff_file_name}_diff
           fi

       done < $diff_file_name

       log_message "INFO" "out of $num_different_files differing files $counter_compressed where tar or compressed and $counter_diffed of those differed"

       if [[ -f ${diff_file_name}_diff ]]; then
        mv  ${diff_file_name}_diff ${diff_file_name}
       fi

       log_message "INFO" "checking if test case has correct number of files"

       baseline_tempfile=${check_baseline_dir_basename}_files.txt
       comrot_tempfile=${comrot_test_dir_basename}_files.txt
       cd $check_baseline_dir_basename
       rm -f ../$baseline_tempfile
       find * -type f > ../$baseline_tempfile
       cd ../$comrot_test_dir_basename
       rm -f ../$comrot_tempfile
       find * -type f > ../$comrot_tempfile
       cd ..
       diff ${baseline_tempfile} ${comrot_tempfile} > /dev/null 2>&1
       if [[ $? != 0 ]]; then
         num_missing_files=0
         while read line; do
          ls ${comrot_test_dir_basename}/$line > /dev/null 2>&1
          if [[ $? != 0 ]]; then
            echo "file $line is in ${check_baseline_dir_basename} but is missing in ${comrot_test_dir_basename}" >> ${diff_file_name}
            num_missing_files=$((num_missing_files+1))
          fi  
         done < $baseline_tempfile
         while read line; do
          ls ${check_baseline_dir_basename}/$line > /dev/null 2>&1
          if [[ $? != 0 ]]; then
            echo "file $line is in ${comrot_test_dir_basename} but is missing in $check_baseline_dir_basename" >> ${diff_file_name}
            num_missing_files=$((num_missing_files+1))
          fi  
         done < $comrot_tempfile
         if [[ $num_missing_files != 0 ]]; then
           log_message "INFO" "$num_missing_files files where either  missing or where unexpected in the test direcotry."
         else
           log_message "INFO" "all the files are accounted for are all the names match in the test directory"
         fi
       else
         log_message "INFO" "all the files are accounted for are all the names match in the test directory"
       fi
       rm -f $baseline_tempfile
       rm -f $comrot_tempfile

       log_message "INFO" "comparing NetCDF files ..."
       find $check_baseline_dir_basename -type f \( -name "*.nc?" -o -name "*.nc" \) > netcdf_filelist.txt
       num_cdf_files=`wc -l < netcdf_filelist.txt`
       counter_identical=0
       counter_differed_nccmp=0
       counter_header_identical=0
       while IFS=/ read netcdf_file; do
         comp_base=`basename $netcdf_file`
         dir_name=`dirname $netcdf_file`
         just_dir=`echo "$dir_name" | sed 's,^[^/]*/,,'`
         file1=$check_baseline_dir_basename/$just_dir/$comp_base ; file2=$comrot_test_dir_basename/$just_dir/$comp_base
         diff $file1 $file2 > /dev/null 2>&1
         if [[ $? != 0 ]]; then
             nccmp_result=$( { $NCCMP --diff-count=4 --threads=4 --data $file1 $file2; } 2>&1) 
             if [[ $? != 0 ]]; then
              counter_differed_nccmp=$((counter_differed_nccmp+1))
              echo "NetCDF file $file1 differs: $nccmp_result" >> $diff_file_name
             else 
              counter_header_identical=$((counter_header_identical+1))
             fi
         else
           counter_identical=$((counter_identical+1))
         fi
       done < netcdf_filelist.txt
       log_message "INFO" "out off $num_cdf_files NetCDF files $counter_identical where completely identical, $counter_header_identical identical data but differed in the header, and $counter_differed_nccmp differed in the data"
       number_diff=`wc -l < $diff_file_name`
       log_message "INFO" "completed running diff for fv3gfs regression test ($regressionID) and found results in file: $diff_file_name"
       log_message "INFO" "out of $total_number_files files, there where $number_diff that differed"
       rm netcdf_filelist.txt

       cd $PWD_start
    fi
}


regressionID_save=$regressionID
if [[ $RUNROCOTO == 'TRUE' ]]; then
    if [[ ! -d ${exp_dir_fullpath} ]]; then
     log_message "CRITICAL" "experiment directory $exp_dir_fullpath not found"
    fi
    log_message "INFO" "running regression script on host $HOST"
    log_message "INTO" "moving to $exp_dir_fullpath to run cycleing in experiment directory"
    cd ${exp_dir_fullpath}

    log_message "INFO" "starting to run fv3gfs cycling regression test run using $rocotoruncmd -d ${pslot}.db -w ${pslot}.xml"
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
       log_message "INFO" "last cycle $lastcycle just reported to be DONE by rocotostat .. exiting execution of workflow"
       break
      fi
      #log_message "INFO" "running: $rocotostatcmd -d ${pslot}.db -w ${pslot}.xml -c all"
      deadjobs=`$rocotostatcmd -d ${pslot}.db -w ${pslot}.xml -c all | awk '$4 == "DEAD" {print $2}'`
      if [[ ! -z $deadjobs ]]; then
         deadjobs=`echo $deadjobs | tr '\n' ' '`
         log_message "CRITICAL" "the following jobs are DEAD: $deadjobs exiting script with error code (-1)"
         exit -1
      fi
      deadcycles=`$rocotostatcmd -d ${pslot}.db -w ${pslot}.xml -c $lastcycle -s | awk '$2 == "Dead" {print $1}'`
      if [[ ! -z $deadcycles ]]; then
       log_message "CRITICAL" "the following cycles are dead: $deadcycles exiting script with error code (-2)"
       exit -2
      fi
      $rocotoruncmd -d ${pslot}.db -w ${pslot}.xml
      if [[ $? == "0" ]]; then
       last_succeeded=`$rocotostatcmd -d ${pslot}.db -w ${pslot}.xml -c all | awk '$4 == "SUCCEEDED" {print $1"_"$2}' | tail -1`
       log_message "INFO" "Successfully ran: $rocotoruncmd -d ${pslot}.db -w ${pslot}.xml"
       #log_message "INFO" "using job level checking: last succeded task checked: $last_succeeded_checked"
       #log_message "INFO" "using job level checking: last succeded task current: $last_succeeded"
       if [[ ! -z $last_succeeded && ! -z last_succeeded_checked ]]; then
         if [[ $last_succeeded != $last_succeeded_checked ]]; then
               last_succeeded_checked=$last_succeeded
               regressionID=$last_succeeded
               log_message "INFO" "job $last_succeeded just completed successfully" 
               if [[ $JOB_LEVEL_CHECK == 'TRUE' ]]; then
                   #run_file_compare_python
                   log_message "WARNING" "job level file compare set but does is not supported yet (the message is here to test logic for running it)"
               fi
         fi
       fi
      else 
       log_message "WARNING" "FAILED: $rocotoruncmd -d ${pslot}.db -w ${pslot}.xml"
      fi

      # Wait here to before running rocotorun again ...
      log_message "INFO" "Waiting here for $ROCOTO_WAIT_FRQUANCY ..."
      sleep $ROCOTO_WAIT_FRQUANCY 

#      if [[ ! -z $RZDM ]]; then
#        viewer_arg_str="-d ${pslot}.db -w ${pslot}.xml --html=$RZDM"
#        cd ${exp_dir_fullpath}
#        $ROCOTOVIEWER $viewer_arg_str
#        if [[ $? == "0" ]]; then 
#          log_message "INFO" "state of workflow posted at $RZDM"
#        else
#          log_message "WARNING" "attempt to write stats to the rzdm server failed"
#        fi
#      fi

   done
   log_message "INFO" "rocotorun completed successfully"
fi

regressionID=$regressionID_save
if [[ $COMPARE_BASE == 'TRUE' ]]; then
  if [[ $PYTHON_FILE_COMPARE == 'TRUE' ]]; then
    run_file_compare_python
  else
    run_file_compare
  fi
fi  

DATE=`date`
if [[ ! -z $number_diff ]]; then
    if [[ $number_diff == 0 ]]; then
      log_message "INFO" "regression tests script completed successfully on $DATE with no file differences"
    else
        if (( $number_diff > 500 )); then
          some="many"
        elif (( $number_diff < 100 )); then
          some="some"
        else
          some="several"
        fi
      log_message "INFO" "regression tests script completed successfully on $DATE with $some file differences"
    fi
fi
SCRIPT_ENDTIME=$(date +%s)
PROCESSTIME=$(($SCRIPT_ENDTIME-$SCRIPT_STARTTIME))
log_message "INFO" "total process time $PROCESSTIME seconds"
