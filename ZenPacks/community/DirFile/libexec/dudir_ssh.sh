#!/bin/bash
#
# Use du to get used for a directory in bytes. 
# Param 1 = ssh user
# Param 2 = keypath
# Param 3 = target
# Param 4 = directory

echo $1 $2 $3 $4 > /tmp/dudir.tmp
#ssh -l zenplug -i ~/.ssh/id_dsa taplow-11 /usr/bin/du -P -b -s /opt/zenoss/local/fredtest | cut -f 1
#ssh -l "$1" -i "$2" "$3"  /usr/bin/du -P -b -s "$4" | cut -f 1
ssh -l "$1" -i "$2" "$3"  /usr/bin/du -P -b -s "$4" 
