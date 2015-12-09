#!/bin/bash
#
# Author:               Jane curry
# Date:                 December 2nd 2015
# Updated:
# First parameter is filename to search for strings
# Second parameter is string to search for
#
# Nagios return codes
#set -x
STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2
STATE_UNKNOWN=3
#
exitstatus=$STATE_OK

filename="$1"
string1="$2"
# Check that command is valid
stringCount1=$(grep "$string1" $filename 2>/dev/null )
if [ "$?" != 0 ]
then
    echo "Error collecting file stats"
    exit $STATE_WARNING
else
    stringCount1=$(grep "$string1" $filename | wc -l )
fi    

echo " File string count test ok | matches=$stringCount1"
exit $exitstatus

