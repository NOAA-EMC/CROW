#### . ${NWROOT:?}/versions/${model:?}.ver
. /gpfs/hps/nco/ops/nwprod/versions/${model:?}.ver
eval export HOME${model}=${NWROOT}/${model}.\${${model}_ver:?}
#### export model=gfs
export PARA_CONFIG=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/fake_para_config
export gfs_ver=v15.0.0
#### export gdas_ver=v15.0.0
#### export global_shared_ver=v15.0.0
#export HOMEgfs=/gpfs/hps3/emc/global/noscrub/emc.glopara/svn/gfs/q3fy17_final/gfs.v15.0.0
##export HOMEgfs=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/fv3/git/fv3gfs/gfs.v15.0.0
#### export HOMEgfs=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/fv3/git/master_20180113/gfs.v15.0.0

export HOMEgfs=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/fv3/git/fv3gfs_flat/gfs.v15.0.0

#export HOMEgdas=/gpfs/hps3/emc/global/noscrub/emc.glopara/svn/gfs/q3fy17_final/gdas.v15.0.0
##export HOMEgdas=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/fv3/git/fv3gfs/gdas.v15.0.0
#### export HOMEgdas=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/fv3/git/master_20180113/gdas.v15.0.0
#export HOMEglobal_shared=/gpfs/hps3/emc/global/noscrub/emc.glopara/svn/gfs/q3fy17_final/global_shared.v15.0.0
##export HOMEglobal_shared=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/fv3/git/fv3gfs/global_shared.v15.0.0
#### export HOMEglobal_shared=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/fv3/git/master_20180113/global_shared.v15.0.0
#### export HOMEobsproc_global=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/obsproc_global.v3.0.0
#### export HOMEobsproc_network=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/obsproc_global.v3.0.0
#### export HOMEobsproc_network=/gpfs/hps3/emc/global/noscrub/emc.glopara/svn/obsproc/releases/obsproc_global_RB-3.0.0
#### export HOMEobsproc_prep=/gpfs/hps3/emc/global/noscrub/emc.glopara/ecflow/obsproc_prep.v4.0.0
#### export HOMEobsproc_prep=/gpfs/hps3/emc/global/noscrub/emc.glopara/svn/obsproc/releases/obsproc_prep_RB-4.0.0
