#!/bin/bash
#
# Runs command, file_stats.sh,  on remote target to return number of lines 
#    in file containing "test 1" and "without"
# file_stats.sh expects one parameter - filename
#
# Returned output in format:
#  " File string count test ok | $string1Name=$stringCount1 $string2Name=$stringCount2"
#  or error output starting with "Error"
#
# Param 1 = ssh user
# Param 2 = keypath
# Param 3 = target
# Param 4 = file to test
# Param 5 = path to file_stats.sh
#set -x

echo $1 $2 $3 $4 $5 > /tmp/filestats.tmp
CMD="$5/file_stats.sh $4"
# ssh -l zenplug -i ~/.ssh/id_dsa taplow-11 /home/zenplug/file_stats.sh /opt/zenoss/local/fredtest/fred1.log_20151202 | cut -f 1
ssh -l "$1" -i "$2" "$3"  "$CMD"
