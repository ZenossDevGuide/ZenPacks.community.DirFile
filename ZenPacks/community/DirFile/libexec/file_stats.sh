#!/bin/bash
#
# Author:               Jane curry
# Date:                 December 2nd 2015
# Updated:
# First parameter is filename to search for strings
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
# Substitute spaces for _
string1="test 1"
string1Name=`echo $string1 | sed -e 's/ /_/g'`
string2="without"
string2Name=`echo $string2 | sed -e 's/ /_/g'`
# Check that command is valid
stringCount1=$(grep "$string1" $filename 2>/dev/null )
if [ "$?" != 0 ]
then
    echo "Error collecting file stats"
    exit $STATE_WARNING
else
    stringCount1=$(grep "$string1" $filename | wc -l )
fi    
# Check that command is valid
stringCount2=$(grep "$string2" $filename 2>/dev/null )
if [ "$?" != 0 ]
then
    echo "Error collecting file stats"
    exit $STATE_WARNING
else
    stringCount2=$(grep "$string2" $filename | wc -l )
fi    

echo " File string count test ok | $string1Name=$stringCount1 $string2Name=$stringCount2"
exit $exitstatus

