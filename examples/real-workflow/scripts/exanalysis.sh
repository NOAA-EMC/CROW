#! /bin/sh

set -xue

cp -fp "$COMINtest"/member*grid .

$CROW_TO_SH namelist:analysis.namelist > post.nl
$CROW_TO_SH run:analysis.command

cp -fp analysis.grid "$COMOUTtest/."
