#!/bin/bash
#
# Use du to get used for a directory in bytes. 
# Then do ls -l in dir
# Param 1 = ssh user
# Param 2 = keypath
# Param 3 = target
# Param 4 = directory

echo $1 $2 $3 $4 > /tmp/dudirls.tmp
#ssh -l zenplug -i ~/.ssh/id_dsa taplow-11 /usr/bin/du -P -b -s /opt/zenoss/local/fredtest;/bin/ls -l "$4 
ssh -l "$1" -i "$2" "$3"  /usr/bin/du -P -b -s "$4";/bin/ls -l "$4"
#ssh -l "$1" -i "$2" "$3"  /bin/ls -l "$4"
