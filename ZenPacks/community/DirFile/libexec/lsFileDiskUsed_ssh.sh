#!/bin/bash
#
# Use ls to get disk used for a file
# Param 1 = ssh user
# Param 2 = keypath
# Param 3 = target
# Param 4 = directory containing file

#set -x
echo $1 $2 $3 $4 > /tmp/lsFileDiskUsed.tmp
#ssh -l zenplug -i ~/.ssh/id_dsa taplow-11 /bin/ls -l  /opt/zenoss/local/fredtest 
ssh -l "$1" -i "$2" "$3"  /bin/ls -l "$4"
