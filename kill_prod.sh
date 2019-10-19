#!/bin/bash
# kill_prod.sh

PID=`ps -eaf | grep bot_chaddi | grep -v grep | awk '{print $2}'`

if [[ "" !=  "$PID" ]]; then
  echo "killing $PID"
  kill -9 $PID
fi