#!/bin/bash
#
# Use df to get disk free.  Get result in bytes (-B 1) and use Posix flag for compatibility.
# Check 6th whitespace separated field for /
#   output 3rd field (Used in Bytes) and make sure no duplicate lines

df -P -B 1 | awk -F " " '$6~/^\/$/ {print $3}' | uniq

