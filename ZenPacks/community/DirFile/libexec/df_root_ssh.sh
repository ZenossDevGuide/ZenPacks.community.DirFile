#!/bin/bash
#
# Use df to get disk free.  
# Param 1 = ssh user
# Param 2 = keypath
# Param 3 = target

#Get result in bytes (-B 1) and use Posix flag for compatibility.
# Check 6th whitespace separated field for /
#   output 3rd field (Used in Bytes) and make sure no duplicate lines

ssh -l "$1" -i "$2" "$3" df -P -B 1 | awk -F " " '$6~/^\/$/ {print $3}' | uniq
