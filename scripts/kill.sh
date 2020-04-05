#!/bin/bash
# kill_chaddi.sh

PID=`ps -eaf | grep chaddi_bot | grep -v grep | awk '{print $2}'`

if [[ "" !=  "$PID" ]]; then
  echo "killing $PID"
  kill -9 $PID
fi