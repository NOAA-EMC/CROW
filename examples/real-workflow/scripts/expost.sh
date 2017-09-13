#! /bin/sh

set -xue

eval $( $CROW_TO_SH scope:post \
          FCST_LEN=fcst_len_hrs \
          DT_WRITE=dt_write_fcst_hrs \
          SLEEP_WAIT=sleep_wait \
          MIN_SIZE=min_size \
          MIN_AGE=min_age \
          MAX_WAIT_STEPS=(max_wait+sleep_wait-1)//sleep_wait \
      )

FHR=0
while [[ "$FHR" -le "$FCST_LEN" ]] ; do
    TO_SH_FHR="$CROW_TO_SH scope:post apply:fhr=$FHR"

    eval $( $TO_SH_FHR INFILE_BASE=infile )
    OUTFILE_BASE=$( echo $INFILE_BASE \
        | sed 's,fcst,post,g' | sed 's,grid,txt,g' )

    INFILE="$COMINtest/$INFILE_BASE"
    OUTFILE="$COMOUTtest/$OUTFILE_BASE"

    $USHtest/wait_for_file.sh "$INFILE" "$MIN_SIZE" "$MIN_AGE" \
        "$SLEEP_WAIT" "$MAX_WAIT_STEPS"

    $TO_SH_FHR namelist:post.namelist > post.nl
    $TO_SH_FHR run:post.command > outfile

    cp -fp outfile "$OUTFILE"
done
