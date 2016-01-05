#!/bin/bash
#
# Use du to get disk used for a directory in bytes. 
# Param 1 = ssh user
# Param 2 = keypath
# Param 3 = target
# Param 4 = file

echo $1 $2 $3 $4 > /tmp/dufile.tmp
#ssh -l zenplug -i ~/.ssh/id_dsa taplow-11 /usr/bin/du -P -b  /opt/zenoss/local/fredtest/fred1.log_20151202 | cut -f 1
ssh -l "$1" -i "$2" "$3"  /usr/bin/du -P -b  "$4" | cut -f 1