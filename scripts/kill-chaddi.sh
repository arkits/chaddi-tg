#!/bin/bash
# kill_chaddi.sh

PID=$(ps -eaf | grep chaddi | grep -v grep | awk '{print $2}')

if [[ "" != "$PID" ]]; then
    echo ">>> Killing PID - $PID"
    kill -9 $PID
fi
