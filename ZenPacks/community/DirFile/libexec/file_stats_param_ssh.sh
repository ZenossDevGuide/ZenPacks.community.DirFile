#!/bin/bash
#
# Runs command, file_stats_param.sh,  on remote target to return number of lines 
#    in file containing supplied string parameter
# file_stats_param.sh expects two parameters - filename and string
#
# Returned output in format:
#  " File string count test ok | matches= $stringCount1
#  or error output starting with "Error"
#
# Param 1 = ssh user
# Param 2 = keypath
# Param 3 = target
# Param 4 = file to test
# Param 5 = path to file_stats.sh
# Param 6 = string to search for
#set -x

echo "$1 $2 $3 $4 $5 $6" > /tmp/filestatsparam.tmp
# Ensure that the string is quoted to preserve spaces
CMD="$5/file_stats_param.sh $4 \"$6\""
# file_stats_param_ssh.sh zenplug  ~/.ssh/id_dsa taplow-11  /opt/zenoss/local/fredtest/fred1.log_20151202 /home/zenplug "test 2"
ssh -l "$1" -i "$2" "$3"  "$CMD"
