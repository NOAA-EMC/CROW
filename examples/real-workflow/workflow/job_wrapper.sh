#! /bin/sh

module purge
module use /scratch4/NCEPDEV/nems/noscrub/emc.nemspara/python/modulefiles/
module load python/3.6.1-emc
module load intel
module load impi

set -xue

cd "$SCRUB_DIR"
"$HOMEtest/jobs/$1"
