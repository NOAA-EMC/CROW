
if ( ! which ecflow_client ) ; then
  module load ecflow
fi

export ECF_NAME=%ECF_NAME%
export ECF_PORT=%ECF_PORT%
export ECF_HOST=%ECF_HOST%
export ECF_PASS=%ECF_PASS%
export ECF_TRYNO=%ECF_TRYNO%
ecflow_client --init=$$

ERROR() {
  set +eu
  set -x
  ecflow_client --abort="Fail with status '$1'"
  trap -
  exit 1
}
trap 'ERROR $?' ERR EXIT TERM USR2 USR1 QUIT

