set -xe  # print commands as they are executed and enable signal trapping

# Variables needed for communication with ecFlow version %ECF_VERSION%
export ECF_NAME=%ECF_NAME%
#export ECF_NODE=%ECF_NODE%
export ECF_NODE=%ECF_LOGHOST%
export ECF_PORT=%ECF_PORT%
export ECF_PASS=%ECF_PASS%
export ECF_TRYNO=%ECF_TRYNO%
export ECF_RID=$LSB_JOBID

# Tell ecFlow we have started
if [ -d /opt/modules ]; then
    . /opt/modules/default/init/sh
else
    . /usrx/local/Modules/default/init/sh
fi
module load ecflow
ecflow_client --init=${ECF_RID}

## Enable LSF to communicate with ecFlow
if [ -d /var/lsf ]; then  # IBM iDataPlex nodes
  POST_OUT=/var/lsf/ecflow_post_in.$LSB_BATCH_JID
else  # Cray XC40 nodes
  POST_OUT=${POST_OUT:-/gpfs/hps/tmpfs/ecflow/ecflow_post_in.$LSB_BATCH_JID}
fi
cat > $POST_OUT <<ENDFILE
ECF_NAME=${ECF_NAME}
ECF_NODE=${ECF_NODE}
ECF_PORT=${ECF_PORT}
ECF_PASS=${ECF_PASS}
ECF_TRYNO=${ECF_TRYNO}
ECF_RID=${ECF_RID}
ENDFILE

# Define error handler
ERROR() {
  set +ex
  if [ "$1" -eq 0 ]; then
     msg="Killed by signal (likely via bkill)"
  else
     msg="Killed by signal $1"
  fi
  ecflow_client --abort="$msg"
  echo $msg
  echo "Trap Caught" >>$POST_OUT
  trap $1; exit $1
}
# Trap all error and exit signals
trap 'ERROR $?' ERR EXIT

